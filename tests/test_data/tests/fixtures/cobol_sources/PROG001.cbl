       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROG001.
       
       ENVIRONMENT DIVISION.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-COUNTER    PIC 9(4).
       01  WS-RESULT     PIC 9(8).
       
       PROCEDURE DIVISION.
           COPY COPY001.
           
           CALL "PROG002" USING WS-COUNTER
                               WS-RESULT.
           
           GOBACK. 