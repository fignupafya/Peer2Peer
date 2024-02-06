import os
import math
import json
import socket
from time import sleep
import threading
from datetime import datetime


broadcast_ip = "25.255.255.255"



#Dont change if not said so

downloads = []
uploads = []
chunks = []

chunknum = 5
file_ext = "png"
broadcast_port = 5001
TCP_port = 5000
brodcast_delay = 60
listen_ip = "0.0.0.0"

# {"tree_1" : [ip1, ip2, ip3....] , "minions_1" : [ip1, ip2, ip3....]     ....}
content_dictionary = {}

proceed = False










def download_bar(current_chunk):
    done = "█"
    not_done = "▒"
    num = current_chunk * 100 / chunknum
    num -= num % 10
    num = int(num/10)
    print("\r"+num*done + (10 - num)*not_done + " %" + str(num*10) , end="")





#Used at Chunk_Announcer and Chunk_Downloader functions
def chunk_finder():
    global chunks
    chunks = []
    for file in os.listdir():
        for number in range(1,chunknum + 1):
            if file.endswith("_"+str(number)):
                if file not in chunks:
                    chunks.append(file)


#Announce-----------------------------------------------------------------



#tree.png -> content_name = tree
def file_divider(content_name):
    global chunks
    filename = content_name + f".{file_ext}"

    try:
        c = os.path.getsize(filename)
    except Exception as e:
        print(f"\nCouldn't get file size: {e}")
        return 0



    CHUNK_SIZE = math.ceil(math.ceil(c) / chunknum)

    index = 1
    chunk_count = 0
    try:
        with open(filename, 'rb') as infile:
            chunk = infile.read(int(CHUNK_SIZE))
            while chunk:
                chunkname = content_name + '_' + str(index)
                try:
                    with open(chunkname, 'wb+') as chunk_file:
                        chunk_file.write(chunk)
                        chunk_count += 1
                        chunks.append(chunkname)
                except Exception as e:
                    print(f"\nChunk creation failed: {chunkname} Error: {e}")
                index += 1
                chunk = infile.read(int(CHUNK_SIZE))
    except Exception as e:
        print(f"\nFile \"{filename}\" couldn't be opened. Error: {e}")
        return 0

    print(f"\nFile is divided into {chunk_count} chunks: ")


    #informing the user about chunk fivision
    informer_text = ""
    for i in range (1,chunknum + 1):
        informer_text+=f"{content_name}_{i} "
    informer_text += "are created. \n"
    print(informer_text)

    return 1

#udp_broadcast
def Chunk_Announcer():
    global proceed



    file_to_host = input("\nWhich file would you like to divide and host?\nLeave blank to host existing chunks only: ").strip()
    proceed = True

    if file_to_host:
        file_divider(file_to_host)
    chunk_finder()
    while True:
        try:
            json_chunks = json.dumps({"chunks": chunks})

            # Create a UDP socket
            # AF_INET represents ipv4
            # SOCK_DGRAM represents UDP type
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Enable broadcasting on the socket
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Send the UDP message to the broadcast IP
            # We encode the json_chunks to send it with udp
            sock.sendto(json_chunks.encode(), (broadcast_ip, broadcast_port))
            sock.close()


        except Exception as e:
            print(f"\nUdp broadcast failed {e}")

        sleep(brodcast_delay)


#Discovery--------------------------------------------------------------



def get_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # connect to a known address
    # It switches to Hamachi ip when available automatically due to using the ip "255.255.255.255"
    sock.connect(("255.255.255.255", 80))

    # getsockname() returns the IP address and the port which the message is sent from
    ip_address = sock.getsockname()[0]

    sock.close()

    return  ip_address

my_ip = get_ip()

def parser(json_text, sender_ip):
    global content_dictionary

    recieved_chunks = json.loads(json_text)["chunks"]

    for chunk in recieved_chunks:

        #checks if the chunk key exists in content dictionary
        if chunk not in content_dictionary.keys():
            content_dictionary[chunk] = []

        #if chunk not already exist in the dictionary:
        if sender_ip not in content_dictionary[chunk]:
            content_dictionary[chunk].append(sender_ip)






#listen_broadcast
def Content_Discovery():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # set socket options to allow broadcasting
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Listens from all interfaces with "0.0.0.0"
        sock.bind((listen_ip, broadcast_port))

        while True:
            # receive data and address from the socket
            data, sender_info = sock.recvfrom(1024)
            # sender_info containts a tuple of sender information (ip,port)

            if sender_info[0] != my_ip:
                parser(data.decode(), sender_info[0])

    except Exception as e:
        print(f"\n\nError: {e}")


#Download--------------------------------------------------------------



def TCP_download(ip, chunkname):





    try:
        json_request = json.dumps({"requested_content": chunkname})

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client_socket.connect((ip, TCP_port))

        client_socket.sendall(json_request.encode())

        file_data = b''

        while True:
            # client_socket.recv(1024) returns  (b'') if connection is closed else it delays the code until new data arrives
            recieved_data_part = client_socket.recv(1024)  # Receive up to 1024 bytes at a time

            if not recieved_data_part:
                break  # No more data to receive
            file_data += recieved_data_part



        try:
            with open(chunkname, 'wb+') as chunk_to_save:
                chunk_to_save.write(file_data)
        except Exception as e:
            print(f"\nChunk \"{chunkname}\" couldn't be saved:  {e}")
            return 0

        client_socket.close()

        #LOGGING
        current_time = datetime.now().time()
        current_time = current_time.strftime("%H:%M:%S")
        dosya = open("LOG.txt", "a", encoding="utf-8")
        dosya.write(f"File downloaded:    Time: {current_time}, File: {chunkname}, IP: {ip}\n")
        return 1

    except Exception as e:
        print(f"\n\nError: {e}")
        return 0

#tree.png -> content_name = tree
def file_merger(content_name):
    chunknames = [f"{content_name}_{i}" for i in range(1, chunknum + 1)]
    missing_chunks=""
    for chunk in chunknames:

        if not os.path.exists(chunk):
            missing_chunks += chunk + ", "
    if missing_chunks:
        print("Missing chunks: " + missing_chunks)
        return 0

    try:
        with open( content_name + f".{file_ext}", 'wb') as outfile:
            for chunk in chunknames:
                try:
                    with open(chunk, 'rb') as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    print(f"\nChunk \"{chunk}\" couldn't be opened {e}")
                    return 0
    except Exception as e:
        print(f"\nFile \"{content_name}.{file_ext}\" couldn't be opened. Error: {e}")
        return 0


    return 1

def Chunk_Downloader():

    while not proceed:
        sleep(0.1)

    while True:

        filestodownload = input("\nWhich content/contents (seperate each filename by space) do you want to download? \n(Leave empty to not downlaod anything) : \n\n").split(" ")

        if filestodownload[0] != '':

            for file in filestodownload:
                if file.endswith(f".{file_ext}"):
                    file = file.rstrip(f".{file_ext}")
                download_bar(0)
                for i in range(1, chunknum + 1):

                    try:
                        chunkname = f"{file}_{i}"
                        hosts = content_dictionary[chunkname]
                        host_count = len(hosts)

                        index = 0
                        for ip in hosts:
                            if TCP_download(ip, chunkname):
                                download_bar(i)
                                break
                            index += 1
                        if index == host_count:
                            print(f"\nCHUNK {chunkname} CANNOT BE DOWNLOADED FROM ONLINE PEERS.")
                    except Exception as e:
                        print(f"\n\nError: {e}")

                if file_merger(file):
                    print(f"\nThe file {file}.{file_ext} has been successfully installed")

                chunk_finder()




        choice = input("\nDo you want to download file(s)?: (y/n) : \n\n").lower().strip()

        while choice != "y" and choice != "n":
            print("Wrong input")
            choice = input("\nDo you want to download file(s)?: (y/n) : \n\n").lower().strip()


        if choice == "n":
            print("\n\nOnly upload mode activated. \n\n")
            break



#Upload-----------------------------------------------------------------


def Chunk_Uploader():


    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind(("", TCP_port))

    server_socket.listen(1)


    while True:
        client_socket, client_ip_port = server_socket.accept()

        request = client_socket.recv(1024).decode()
        try:
            requested_file = json.loads(request)["requested_content"]
            try:
                with open(requested_file, 'rb') as file:
                    file_data = file.read()
                    client_socket.sendall(file_data)
                    client_socket.close()

                    print(f"Requested file {requested_file} served to {client_ip_port[0]}")

                    # LOGGING
                    current_time = datetime.now().time()
                    current_time = current_time.strftime("%H:%M:%S")
                    dosya = open("LOG.txt", "a", encoding="utf-8")
                    dosya.write(f"File uploaded:      Time: {current_time}, File: {requested_file}, IP: {client_ip_port[0]}\n")
                    dosya.close()



            except Exception as e:
                print(f"\nFile operation error {e}")


        except Exception as e:
            print(f"\nBad formatted request  Error: {e}")












#Main-----------------------------------------------------------------

banner="""
        ____                ___   ____                
       / __ \___  ___  ____|__ \ / __ \___  ___  _____
      / /_/ / _ \/ _ \/ ___/_/ // /_/ / _ \/ _ \/ ___/
     / ____/  __/  __/ /  / __// ____/  __/  __/ /    
    /_/    \___/\___/_/  /____/_/    \___/\___/_/     """


print()
print(banner)
print()

t1 = threading.Thread(target=Content_Discovery)
t2 = threading.Thread(target=Chunk_Announcer)
t3 = threading.Thread(target=Chunk_Uploader)
t1.start()
t2.start()
t3.start()

Chunk_Downloader()






