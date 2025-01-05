-- AST データのサンプル
INSERT INTO ast_nodes (program_id, node_type, node_value, parent_id) VALUES
('PROG001', 'PROGRAM-ID', 'PROG001', NULL),
('PROG001', 'CALL', 'PROG002', 1),
('PROG001', 'COPY', 'COPY001', 1); 