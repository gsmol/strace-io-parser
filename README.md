Simple strace output analyzer 


Sample usage:

```
strace -f -p PID_OF_PROCESS -o strace.log
(Ctrl-C)

./strace-io-parser.py strace.log
