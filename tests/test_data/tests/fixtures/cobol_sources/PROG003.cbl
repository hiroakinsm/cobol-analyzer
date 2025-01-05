       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROG003.
       
       ENVIRONMENT DIVISION.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-WORK-AREA    PIC X(100).
       
       LINKAGE SECTION.
       01  LS-CALC-AREA.
           05  LS-INPUT     PIC 9(4).
           05  LS-OUTPUT    PIC 9(8).
       
       PROCEDURE DIVISION USING LS-CALC-AREA.
           COPY COPY003.
           
           GOBACK. 