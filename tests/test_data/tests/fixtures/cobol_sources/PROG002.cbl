       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROG002.
       
       ENVIRONMENT DIVISION.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-CALC-AREA.
           05  WS-INPUT     PIC 9(4).
           05  WS-OUTPUT    PIC 9(8).
       
       LINKAGE SECTION.
       01  LS-INPUT        PIC 9(4).
       01  LS-RESULT       PIC 9(8).
       
       PROCEDURE DIVISION USING LS-INPUT LS-RESULT.
           COPY COPY002.
           
           CALL "PROG003" USING WS-CALC-AREA.
           
           GOBACK. 