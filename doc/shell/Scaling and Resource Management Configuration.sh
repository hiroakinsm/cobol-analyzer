#!/bin/bash

# スケーリングと負荷分散の設定

# 基本設定
SCALING_ROOT="/home/administrator/scaling"
mkdir -p ${SCALING_ROOT}/{config,scripts,logs}

# リソース制御設定
cat << EOF > ${SCALING_ROOT}/config/resource_limits.yaml
resource_limits:
  application_server:  # 172.16.0.27
    cpu_limit: 16      # 物理コア数に応じて
    memory_limit: "14G"  # 16GBの約85%を上限に設定
    max_connections: 50
    timeout: 300
    
  ai_server:  # 172.16.0.19
    cpu_limit: 16
    memory_limit: "28G"  # 32GBの約85%を上限に設定
    gpu_memory_limit: "7G"  # 8GBの約85%を上限に設定
    max_parallel_inferences: 2  # GPUメモリに合わせて調整
    batch_size: 4
    timeout: 600

  databases:
    postgresql:  # 172.16.0.13
      max_connections: 50
      shared_buffers: "4GB"
      effective_cache_size: "12GB"
      maintenance_work_mem: "1GB"
      
    mongodb:  # 172.16.0.17
      max_connections: 50
      wired_tiger_cache_size: "8GB"  # メモリの50%程度

      
  task_queues:
    analysis_queue:
      max_size: 1000
      workers: 4
      priority_levels: 3
    
    rag_queue:
      max_size: 500
      workers: 2
      priority_levels: 2

EOF

# タスクキューの設定
cat << EOF > ${SCALING_ROOT}/config/task_queue_config.py
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any
import asyncio
import logging

class TaskPriority(Enum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2

@dataclass
class TaskConfig:
    priority: TaskPriority
    timeout: int
    retries: int
    backoff_factor: float

class TaskQueue:
    def __init__(self, max_size: int, workers: int):
        self.queue = asyncio.PriorityQueue(maxsize=max_size)
        self.workers = workers
        self.tasks = set()
        self.logger = logging.getLogger(__name__)

    async def submit(self, task, priority: TaskPriority):
        await self.queue.put((priority.value, task))
        self.logger.info(f"Task submitted with priority {priority}")

    async def process_task(self, task):
        try:
            result = await task.execute()
            self.logger.info(f"Task completed: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Task failed: {str(e)}")
            if task.retries > 0:
                task.retries -= 1
                await asyncio.sleep(task.backoff_factor * (3 - task.retries))
                await self.submit(task, task.priority)

    async def start_workers(self):
        workers = [self.worker(i) for i in range(self.workers)]
        await asyncio.gather(*workers)

    async def worker(self, worker_id: int):
        while True:
            priority, task = await self.queue.get()
            self.logger.info(f"Worker {worker_id} processing task")
            try:
                await self.process_task(task)
            finally:
                self.queue.task_done()
EOF

# CPU制限の設定スクリプト
cat << EOF > ${SCALING_ROOT}/scripts/set_cpu_limits.sh
#!/bin/bash

# CPUset制御
setup_cpuset() {
    local service=\$1
    local cpu_list=\$2
    
    # cgroup設定
    sudo mkdir -p /sys/fs/cgroup/cpuset/\${service}
    echo \${cpu_list} | sudo tee /sys/fs/cgroup/cpuset/\${service}/cpuset.cpus
    echo "0" | sudo tee /sys/fs/cgroup/cpuset/\${service}/cpuset.mems
}

# CPU制限の適用
setup_cpuset "cobol-analyzer" "0-15"  # CPU 0-15をアプリケーションサーバーに割り当て
setup_cpuset "rag-system" "16-31"     # CPU 16-31をRAGシステムに割り当て
EOF

# メモリ制限の設定スクリプト
cat << EOF > ${SCALING_ROOT}/scripts/set_memory_limits.sh
#!/bin/bash

# メモリ制限の設定
setup_memory_limit() {
    local service=\$1
    local memory_limit=\$2
    
    # cgroup設定
    sudo mkdir -p /sys/fs/cgroup/memory/\${service}
    echo \${memory_limit} | sudo tee /sys/fs/cgroup/memory/\${service}/memory.limit_in_bytes
}

# メモリ制限の適用
setup_memory_limit "cobol-analyzer" "28G"
setup_memory_limit "rag-system" "28G"
EOF

# GPU制限の設定スクリプト
cat << EOF > ${SCALING_ROOT}/scripts/set_gpu_limits.sh
#!/bin/bash

# NVIDIA GPU制限の設定
setup_gpu_limit() {
    local service=\$1
    local memory_limit=\$2
    
    # nvidia-smiを使用してGPUメモリ制限を設定
    nvidia-smi --gpu-reset-file=/tmp/gpu_reset
    nvidia-smi -pl \${memory_limit}
}

# GPU制限の設定（AI/RAGサーバーのみ）
if [ "$(hostname -I | tr -d ' ')" = "172.16.0.19" ]; then
    # 8GB GPU用の設定
    setup_gpu_limit "rag-system" "7168" # 7GB in MB
fi
EOF

# 負荷監視とスケーリング制御スクリプト
cat << EOF > ${SCALING_ROOT}/scripts/scaling_controller.py
import asyncio
import psutil
import gpustat
import logging
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ResourceMetrics:
    cpu_usage: float
    memory_usage: float
    gpu_usage: float
    queue_size: int

class ScalingController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.thresholds = {
            'cpu_high': 80.0,
            'cpu_low': 20.0,
            'memory_high': 85.0,
            'memory_low': 25.0,
            'queue_high': 100,
            'queue_low': 10
        }

    async def collect_metrics(self) -> ResourceMetrics:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        gpu_stats = gpustat.GPUStatCollection.new_query()
        
        return ResourceMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            gpu_usage=gpu_stats[0].memory_used,
            queue_size=self._get_queue_size()
        )

    async def scale_resources(self, metrics: ResourceMetrics):
        if metrics.cpu_usage > self.thresholds['cpu_high']:
            await self._scale_up_cpu()
        elif metrics.cpu_usage < self.thresholds['cpu_low']:
            await self._scale_down_cpu()

        if metrics.memory_usage > self.thresholds['memory_high']:
            await self._scale_up_memory()
        elif metrics.memory_usage < self.thresholds['memory_low']:
            await self._scale_down_memory()

    async def _scale_up_cpu(self):
        self.logger.info("Scaling up CPU resources")
        # CPU制限の緩和
        await self._update_cpu_limit(increase=True)

    async def _scale_down_cpu(self):
        self.logger.info("Scaling down CPU resources")
        # CPU制限の強化
        await self._update_cpu_limit(increase=False)

    async def _scale_up_memory(self):
        self.logger.info("Scaling up memory resources")
        # メモリ制限の緩和
        await self._update_memory_limit(increase=True)

    async def _scale_down_memory(self):
        self.logger.info("Scaling down memory resources")
        # メモリ制限の強化
        await self._update_memory_limit(increase=False)

    async def monitor_and_scale(self):
        while True:
            try:
                metrics = await self.collect_metrics()
                await self.scale_resources(metrics)
                await asyncio.sleep(60)  # 1分間隔でチェック
            except Exception as e:
                self.logger.error(f"Error in monitoring: {str(e)}")
                await asyncio.sleep(60)
EOF

# リソース制限の適用
chmod +x ${SCALING_ROOT}/scripts/*.sh
${SCALING_ROOT}/scripts/set_cpu_limits.sh
${SCALING_ROOT}/scripts/set_memory_limits.sh
${SCALING_ROOT}/scripts/set_gpu_limits.sh

# スケーリングコントローラーのサービス設定
cat << EOF > /etc/systemd/system/scaling-controller.service
[Unit]
Description=Resource Scaling Controller
After=network.target

[Service]
Type=simple
User=administrator
ExecStart=${SCALING_ROOT}/venv/bin/python ${SCALING_ROOT}/scripts/scaling_controller.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable scaling-controller
sudo systemctl start scaling-controller