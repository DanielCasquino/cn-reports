import socket
import zlib
import struct
import time

class Receiver:
    def __init__(self, ip: str = "127.0.0.1", in_port: int = 5006, out_port: int = 5005, timeout=3, log_filename: str = "receiver_log.txt"):
        self.ip = ip
        self.in_port = in_port
        self.out_port = out_port
        self.timeout = timeout
        self.log_filename = log_filename
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)
        self.sock.bind((ip, self.in_port))

    def chksm(self, msg: bytes):
        checksum = zlib.crc32(msg)
        return checksum
    
    def log(self, message, f):
        print(message)
        f.write(f"[{time.strftime('%H:%M:%S')}.{int(time.time() * 1000) % 1000:03d}] {message}\n")
        # gpt

    def simulate_connection(self):
        with open(self.log_filename, "w") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.log("Started connection", f)
            seq = 0

            while True:
                data, addr = self.sock.recvfrom(1024)
                sender_port, receiver_port, length, recv_csum, seq_num = struct.unpack("!IIIII", data[:20])

                msg = data[20:20+length]
                self.log(f"I received: {msg}", f)
                csum = self.chksm(msg)
                
                if csum == recv_csum and seq_num == seq:
                    ack = struct.pack("!I", 1)
                    self.log("Checksum and SEQ correct, ACK", f)
                    seq += 1
                elif csum != recv_csum and seq_num == seq:
                    ack = struct.pack("!I", 0)
                    self.log("Checksum incorrect and SEQ correct, NAK", f)
                elif seq_num != seq:
                    ack = struct.pack("!I", 0)
                    self.log("Checksum correct and SEQ incorrect, NAK", f)
                else:
                    ack = struct.pack("!I", 0)
                    self.log("Checksum and SEQ incorrect, NAK", f)

                self.sock.sendto(ack, (self.ip, self.out_port))

                if (msg == b"END"):
                    break
            self.log("Finished connection", f)

if __name__ == "__main__":
    receiver = Receiver()
    receiver.simulate_connection()
