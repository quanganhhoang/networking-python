Simple networking code using socket API. Client sends a number of arithmetic expressions and server evaluates (without using built_in eval()) and returns the result.
 
A. Protocol Spec
Because the service model provided by stream socket is a reliable stream of bytes (no meaning attached to the data, and no boundary on messages), we need to design an application layer protocol to define the syntax and semantics of the data we send between client and server.

B. Request format

1. Number of expressions to evaluate. [2 bytes, encoded using network endianness]
2. Length of 1st expression in bytes. [2 bytes, encoded using network endianness]
3. String representation of 1st expression. [sequence of bytes]
4. Length of 2nd expression in bytes. [2 bytes, encoded using network endianness]
5. String representation of 2nd expression. [sequence of bytes]
…
Length of nth expression in bytes. [2 bytes, encoded using network endianness]
String representation of nth expression. [sequence of bytes]

C. Response format

1. Number of answers. [2 bytes, encoded using network endianness]
2. Length of 1st answer in bytes. [2 bytes, encoded using network endianness]
3. String representation of 1st answer. [sequence of bytes]
4. Length of 2nd answer in bytes. [2 bytes, encoded using network endianness]
5. String representation of 2nd answer. [sequence of bytes]
…
Length of nth answer in bytes. [2 bytes, encoded using network endianness]
String representation of nth answer. [sequence of bytes]

D. How to run

1. python3 server.py
2. python3 client.py

