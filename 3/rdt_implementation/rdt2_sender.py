import socket
import zlib
import struct
import random
import time


class Sender:
    ACK = 1
    NAK = 0

    def __init__(self, ip: str = "127.0.0.1", in_port: int = 5005, out_port:int = 5006, timeout=0.01, corrupt_prob = 0.4, log_filename: str = "sender_log.txt"):
        self.ip = ip
        self.in_port = in_port
        self.out_port = out_port
        self.timeout = timeout
        self.corrupt_prob = corrupt_prob
        self.log_filename = log_filename
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)
        self.sock.bind((ip, self.in_port))

    def chksm(self, msg: bytes):
        checksum = zlib.crc32(msg)
        return checksum
    
    def get_ack(self, data: bytes):
        ack, = struct.unpack("!I", data)
        if ack == 1:
            return self.ACK
        else:
            return self.NAK

    def try_corrupt(self, msg: bytes):
        if random.random() < self.corrupt_prob:
            if len(msg) == 0:
                return msg
            corr_idx = random.randint(0, len(msg) - 1)
            corr_msg = bytearray(msg) # gg
            corr_msg[corr_idx] = (corr_msg[corr_idx] + 1) % 256
            return bytes(corr_msg), True
        else:
            return msg, False

    def log(self, message, f):
        print(message)
        f.write(f"[{time.strftime('%H:%M:%S')}.{int(time.time() * 1000) % 1000:03d}] {message}\n")
        # gpt

    def simulate_connection(self, packets: list[bytes]):
        with open(self.log_filename, "w") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.log("Started connection", f)

            for i in range(len(packets)):
                pkt = packets[i]
                while True:
                    try:
                        corr_pkt, is_corrupt = self.try_corrupt(pkt)
                        sequence = i
                        if is_corrupt:
                            self.log("Corrupted packet", f)
                            sequence = (i + 1) % random.randint(2, 10) # pueser que se corrompa el seq num XD

                        length: int = len(pkt)
                        csum = self.chksm(pkt)
                        
                        header = struct.pack("!IIIII", self.in_port, self.out_port, length, csum, sequence)
                        final_msg = header + corr_pkt
                        self.sock.sendto(final_msg, (self.ip, self.out_port))
                        self.log(f"I sent: {corr_pkt}", f)

                        data, addr = self.sock.recvfrom(1024)
                        value = self.get_ack(data)
                        if value == self.ACK:
                            self.log("Received ACK", f)
                            break
                        elif value == self.NAK:
                            self.log("Received NAK", f)
                    except socket.timeout:
                        self.log("Timeout, resending", f)
            self.log("Finished connection", f)



if __name__ == "__main__":
    sender = Sender()
    packets_to_send: list[bytes] = [
        b"Never",
        b"Gonna",
        b"Give",
        b"You",
        b"Up",
        b"Never",
        b"Gonna",
        b"Let",
        b"You",
        b"Down",
        b"END"
    ]
    # terrible profe
    sender.simulate_connection(packets_to_send)
