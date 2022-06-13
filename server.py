from cgitb import reset
from encodings import utf_8
from os import system
import socket
import string
import struct
import this
from time import sleep
import random
import threading
import struct
from requests import request

# creste pig class
class Pig:
    def __init__(self):
        self.clean_or_not = True
        self.have_house = False
        self.have_lc = False
        self.door_lock = False

# create card class
class Card:

    all_types = ['mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','mud','house','house','house','house','rain','rain','rain','rain','thunder','thunder','thunder','thunder','lc','lc','lc','lc','door_lock','door_lock','door_lock','door_lock','farmer','farmer','farmer','farmer','farmer','farmer','farmer','farmer']
    def __init__(self):
        self.card_type = self.random_type()[0]
    def random_type(self):#all54
        return random.sample(self.all_types,1)
    def new_one(self):
        self.card_type = self.random_type()[0]

# create player class
class Player:

    def __init__(self, addr, conn, name, user_id):
        self.addr = addr
        self.conn = conn
        self.name = name
        self.id = user_id
        self.pig_list = []
        self.card_list = []
        pig_1 = Pig()
        pig_2 = Pig()
        pig_3 = Pig()
        self.pig_list.append(pig_1)
        self.pig_list.append(pig_2)
        self.pig_list.append(pig_3)
        card_1 = Card()
        card_2 = Card()
        card_3 = Card()
        self.card_list.append(card_1)
        self.card_list.append(card_2)
        self.card_list.append(card_3)

# create game class
class Game:

    def __init__(self):
        self.state = 'waiting_to_start'# waiting_to_start, playing, end``
        self.players = []# list of client
        self.ids = 0# id of players = index 0 1 2 3
        self.current_index = 0# whose turn
        self.current_picked_card_type = None #rain, thunders, mud, house, lc, door_lock, farmer
        self.current_picked_card_ID = None
        self.winner = None

    def boardcast(self, msg):
        print("boardcast to player: " + msg)
        msg_len = len(msg)
        msg_len_bytes = struct.pack('<I', msg_len)
        for i in range(len(self.players)):
            try:
                self.players[i].conn.send(msg_len_bytes)
                self.players[i].conn.send(msg.encode())
            except Exception as e:
                print(e)

    def clean_the_pigs_have_no_house(self):
        for i in range(len(self.players)):
            for j in range(len(self.players[i].pig_list)):
                if self.players[i].pig_list[j].have_house == False:
                    self.players[i].pig_list[j].clean_or_not = True

    def recvall(self, sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            data.extend(packet)
        return data

    def handle_client(self, addr, client, name, userid):
        try:
            join_msg = "join_request"+" "+name
            self.boardcast(join_msg)
            id_msg = "id_set" + " " + str(userid)
            id_msg_len = len(id_msg)
            id_msg_len_bytes = struct.pack('<I', id_msg_len)
            client.send(id_msg_len_bytes)
            client.send(id_msg.encode())
        except Exception as e:
            print(e)
        while True:
            try:
                raw_msglen = self.recvall(client, 4)
                if not raw_msglen:
                    return None
                msglen = struct.unpack('<I', raw_msglen)[0]
                # Read the message data
                msg = self.recvall(client, msglen).decode()
                if userid != self.current_index:
                    continue
                self.submit_request(userid, msg)
            except Exception as e:
                print(e)
                break

    def submit_request(self, user_id, msg):#state = playing
        try:
            msglist = msg.split()
            request = msglist[0]
            if request == "click":
                click_type = msglist[1]
                if click_type == "pig":
                    pig_owner_id = int(msglist[2])
                    pig_id = int(msglist[3])
                    self.click_pig(pig_owner_id, pig_id)
                elif click_type == "hand":
                    card_owner_id = user_id
                    card_id = int(msglist[2])
                    self.click_card(card_owner_id, card_id)
            elif request == "switch":
                self.click_switch()
        except Exception as e:
            print(e)

    def click_switch(self):
        if self.current_picked_card_ID == None:
            self.send_by_id(self.current_index, "no_card_picked")
        else:
            self.next_turn()

    def click_pig(self, pig_owner_id, pig_id):
        try:
            flag = False
            if self.current_picked_card_type == None:
                self.send_by_id(self.current_index, "no_card_picked")
            elif self.current_picked_card_type == "mud":
                if self.players[pig_owner_id].pig_list[pig_id].clean_or_not:
                    self.players[pig_owner_id].pig_list[pig_id].clean_or_not = False
                    flag = True
                else:
                    self.send_by_id(self.current_index, "invalid_move")
            elif self.current_picked_card_type == "rain":
                self.clean_the_pigs_have_no_house()
                flag = True
            elif self.current_picked_card_type == "thunder":
                if self.players[pig_owner_id].pig_list[pig_id].have_house and not (self.players[pig_owner_id].pig_list[pig_id].have_lc):
                    self.players[pig_owner_id].pig_list[pig_id].have_house = False
                    self.players[pig_owner_id].pig_list[pig_id].door_lock = False
                    flag = True
                else:
                    self.send_by_id(self.current_index, "invalid_move")
            elif self.current_picked_card_type == "house":
                if not (self.players[pig_owner_id].pig_list[pig_id].have_house):
                    self.players[pig_owner_id].pig_list[pig_id].have_house = True
                    flag = True
                else:
                    self.send_by_id(self.current_index, "invalid_move")
            elif self.current_picked_card_type == "lc":
                if self.players[pig_owner_id].pig_list[pig_id].have_house:
                    self.players[pig_owner_id].pig_list[pig_id].have_lc = True
                    flag = True
                else:
                    self.send_by_id(self.current_index, "invalid_move")
            elif self.current_picked_card_type == "door_lock":
                if self.players[pig_owner_id].pig_list[pig_id].have_house:
                    self.players[pig_owner_id].pig_list[pig_id].door_lock = True
                    flag = True
                else:
                    self.send_by_id(self.current_index, "invalid_move")
            elif self.current_picked_card_type == "farmer":
                if not self.players[pig_owner_id].pig_list[pig_id].door_lock and not self.players[pig_owner_id].pig_list[pig_id].clean_or_not:
                    self.players[pig_owner_id].pig_list[pig_id].clean_or_not = True
                    flag = True
                else:
                    self.send_by_id(self.current_index, "invalid_move")
            
            if flag:
                self.send_by_id(self.current_index, "move_success")
                self.next_turn()
        except Exception as e:
            print(e)
    

    def reset_game(self):
        self.__init__()
        

    def next_turn(self):
        
        self.players[self.current_index].card_list[self.current_picked_card_ID].new_one()
        self.current_picked_card_type = None
        self.current_picked_card_ID = None
        self.current_index = (self.current_index + 1) % len(self.players)
        #update view
        state_msg = "state_update" + " " + self.view_inform()
        self.boardcast(state_msg)
        sleep(0.5)
        #check if game over
        if self.check_game_over():
            self.boardcast(("game_over"+" "+self.winner))
            self.reset_game()
        #next turn
        else:
            turn_msg = "turn"+" "+str (self.players[self.current_index].name)
            self.boardcast(turn_msg)

    def check_game_over(self):
        for i in range(len(self.players)):
            flag = True
            for j in range(len(self.players[i].pig_list)):
                if self.players[i].pig_list[j].clean_or_not:
                    flag = False
                    break
            if flag:
                self.winner = str(self.players[i].name)
                return True
        return False

    def click_card(self, card_owner_id, card_id):
        try:
            self.current_picked_card_type = self.players[card_owner_id].card_list[card_id].card_type
            self.current_picked_card_ID = card_id
            picked_type = self.current_picked_card_type
            self.send_by_id(self.current_index, "card_picked"+ " " + picked_type)
        except Exception as e:
            print(e)

    def send_by_id(self, id, msg):
        try:
            msg_len = len(msg)
            len_bytes = struct.pack('<I', msg_len)
            self.players[id].conn.send(len_bytes)
            self.players[id].conn.send(msg.encode())
        except Exception as e:
            print(e)

    def create_id(self):
        tmp = self.ids
        self.ids += 1
        return tmp

    def view_inform(self):
        user0_name = str(self.players[0].name)
        user0_id = str(self.players[0].id)
        user0_card0_type = self.players[0].card_list[0].card_type
        user0_card1_type = self.players[0].card_list[1].card_type
        user0_card2_type = self.players[0].card_list[2].card_type
        user0_pig0_clean_or_not = str(self.players[0].pig_list[0].clean_or_not)
        user0_pig0_have_house = str(self.players[0].pig_list[0].have_house)
        user0_pig0_have_lc = str(self.players[0].pig_list[0].have_lc)
        user0_pig0_door_lock = str(self.players[0].pig_list[0].door_lock)
        user0_pig1_clean_or_not = str(self.players[0].pig_list[1].clean_or_not)
        user0_pig1_have_house = str(self.players[0].pig_list[1].have_house)
        user0_pig1_have_lc = str(self.players[0].pig_list[1].have_lc)
        user0_pig1_door_lock = str(self.players[0].pig_list[1].door_lock)
        user0_pig2_clean_or_not = str(self.players[0].pig_list[2].clean_or_not)
        user0_pig2_have_house = str(self.players[0].pig_list[2].have_house)
        user0_pig2_have_lc = str(self.players[0].pig_list[2].have_lc)
        user0_pig2_door_lock = str(self.players[0].pig_list[2].door_lock)
        user1_name = str(self.players[1].name)
        user1_id = str(self.players[1].id)
        user1_card0_type = self.players[1].card_list[0].card_type
        user1_card1_type = self.players[1].card_list[1].card_type
        user1_card2_type = self.players[1].card_list[2].card_type
        user1_pig0_clean_or_not = str(self.players[1].pig_list[0].clean_or_not)
        user1_pig0_have_house = str(self.players[1].pig_list[0].have_house)
        user1_pig0_have_lc = str(self.players[1].pig_list[0].have_lc)
        user1_pig0_door_lock = str(self.players[1].pig_list[0].door_lock)
        user1_pig1_clean_or_not = str(self.players[1].pig_list[1].clean_or_not)
        user1_pig1_have_house = str(self.players[1].pig_list[1].have_house)
        user1_pig1_have_lc = str(self.players[1].pig_list[1].have_lc)
        user1_pig1_door_lock = str(self.players[1].pig_list[1].door_lock)
        user1_pig2_clean_or_not = str(self.players[1].pig_list[2].clean_or_not)
        user1_pig2_have_house = str(self.players[1].pig_list[2].have_house)
        user1_pig2_have_lc = str(self.players[1].pig_list[2].have_lc)
        user1_pig2_door_lock = str(self.players[1].pig_list[2].door_lock)
        user2_name = str(self.players[2].name)
        user2_id = str(self.players[2].id)
        user2_card0_type = self.players[2].card_list[0].card_type
        user2_card1_type = self.players[2].card_list[1].card_type
        user2_card2_type = self.players[2].card_list[2].card_type
        user2_pig0_clean_or_not = str(self.players[2].pig_list[0].clean_or_not)
        user2_pig0_have_house = str(self.players[2].pig_list[0].have_house)
        user2_pig0_have_lc = str(self.players[2].pig_list[0].have_lc)
        user2_pig0_door_lock = str(self.players[2].pig_list[0].door_lock)
        user2_pig1_clean_or_not = str(self.players[2].pig_list[1].clean_or_not)
        user2_pig1_have_house = str(self.players[2].pig_list[1].have_house)
        user2_pig1_have_lc = str(self.players[2].pig_list[1].have_lc)
        user2_pig1_door_lock = str(self.players[2].pig_list[1].door_lock)
        user2_pig2_clean_or_not = str(self.players[2].pig_list[2].clean_or_not)
        user2_pig2_have_house = str(self.players[2].pig_list[2].have_house)
        user2_pig2_have_lc = str(self.players[2].pig_list[2].have_lc)
        user2_pig2_door_lock = str(self.players[2].pig_list[2].door_lock)
        user3_name = str(self.players[3].name)
        user3_id = str(self.players[3].id)
        user3_card0_type = self.players[3].card_list[0].card_type
        user3_card1_type = self.players[3].card_list[1].card_type
        user3_card2_type = self.players[3].card_list[2].card_type
        user3_pig0_clean_or_not = str(self.players[3].pig_list[0].clean_or_not)
        user3_pig0_have_house = str(self.players[3].pig_list[0].have_house)
        user3_pig0_have_lc = str(self.players[3].pig_list[0].have_lc)
        user3_pig0_door_lock = str(self.players[3].pig_list[0].door_lock)
        user3_pig1_clean_or_not = str(self.players[3].pig_list[1].clean_or_not)
        user3_pig1_have_house = str(self.players[3].pig_list[1].have_house)
        user3_pig1_have_lc = str(self.players[3].pig_list[1].have_lc)
        user3_pig1_door_lock = str(self.players[3].pig_list[1].door_lock)
        user3_pig2_clean_or_not = str(self.players[3].pig_list[2].clean_or_not)
        user3_pig2_have_house = str(self.players[3].pig_list[2].have_house)
        user3_pig2_have_lc = str(self.players[3].pig_list[2].have_lc)
        user3_pig2_door_lock = str(self.players[3].pig_list[2].door_lock)
        user0_inform = user0_name+" "+user0_id+" "+user0_card0_type+" "+user0_card1_type+" "+user0_card2_type+" "+user0_pig0_clean_or_not+" "+user0_pig0_have_house+" "+user0_pig0_have_lc+" "+user0_pig0_door_lock+" "+user0_pig1_clean_or_not+" "+user0_pig1_have_house+" "+user0_pig1_have_lc+" "+user0_pig1_door_lock+" "+user0_pig2_clean_or_not+" "+user0_pig2_have_house+" "+user0_pig2_have_lc+" "+user0_pig2_door_lock
        user1_inform = user1_name+" "+user1_id+" "+user1_card0_type+" "+user1_card1_type+" "+user1_card2_type+" "+user1_pig0_clean_or_not+" "+user1_pig0_have_house+" "+user1_pig0_have_lc+" "+user1_pig0_door_lock+" "+user1_pig1_clean_or_not+" "+user1_pig1_have_house+" "+user1_pig1_have_lc+" "+user1_pig1_door_lock+" "+user1_pig2_clean_or_not+" "+user1_pig2_have_house+" "+user1_pig2_have_lc+" "+user1_pig2_door_lock
        user2_inform = user2_name+" "+user2_id+" "+user2_card0_type+" "+user2_card1_type+" "+user2_card2_type+" "+user2_pig0_clean_or_not+" "+user2_pig0_have_house+" "+user2_pig0_have_lc+" "+user2_pig0_door_lock+" "+user2_pig1_clean_or_not+" "+user2_pig1_have_house+" "+user2_pig1_have_lc+" "+user2_pig1_door_lock+" "+user2_pig2_clean_or_not+" "+user2_pig2_have_house+" "+user2_pig2_have_lc+" "+user2_pig2_door_lock
        user3_inform = user3_name+" "+user3_id+" "+user3_card0_type+" "+user3_card1_type+" "+user3_card2_type+" "+user3_pig0_clean_or_not+" "+user3_pig0_have_house+" "+user3_pig0_have_lc+" "+user3_pig0_door_lock+" "+user3_pig1_clean_or_not+" "+user3_pig1_have_house+" "+user3_pig1_have_lc+" "+user3_pig1_door_lock+" "+user3_pig2_clean_or_not+" "+user3_pig2_have_house+" "+user3_pig2_have_lc+" "+user3_pig2_door_lock
        view_inform = user0_inform+" "+user1_inform+" "+user2_inform+" "+user3_inform
        return view_inform

    def check_if_start(self):
        if len(self.players) == 4:
            self.state = 'playing'
            #client innitialize
            user0_name = str(self.players[0].name)
            user0_id = str(self.players[0].id)
            user0_card0_type = self.players[0].card_list[0].card_type
            user0_card1_type = self.players[0].card_list[1].card_type
            user0_card2_type = self.players[0].card_list[2].card_type
            user0_pig0_clean_or_not = str(self.players[0].pig_list[0].clean_or_not)
            user0_pig0_have_house = str(self.players[0].pig_list[0].have_house)
            user0_pig0_have_lc = str(self.players[0].pig_list[0].have_lc)
            user0_pig0_door_lock = str(self.players[0].pig_list[0].door_lock)
            user0_pig1_clean_or_not = str(self.players[0].pig_list[1].clean_or_not)
            user0_pig1_have_house = str(self.players[0].pig_list[1].have_house)
            user0_pig1_have_lc = str(self.players[0].pig_list[1].have_lc)
            user0_pig1_door_lock = str(self.players[0].pig_list[1].door_lock)
            user0_pig2_clean_or_not = str(self.players[0].pig_list[2].clean_or_not)
            user0_pig2_have_house = str(self.players[0].pig_list[2].have_house)
            user0_pig2_have_lc = str(self.players[0].pig_list[2].have_lc)
            user0_pig2_door_lock = str(self.players[0].pig_list[2].door_lock)
            user1_name = str(self.players[1].name)
            user1_id = str(self.players[1].id)
            user1_card0_type = self.players[1].card_list[0].card_type
            user1_card1_type = self.players[1].card_list[1].card_type
            user1_card2_type = self.players[1].card_list[2].card_type
            user1_pig0_clean_or_not = str(self.players[1].pig_list[0].clean_or_not)
            user1_pig0_have_house = str(self.players[1].pig_list[0].have_house)
            user1_pig0_have_lc = str(self.players[1].pig_list[0].have_lc)
            user1_pig0_door_lock = str(self.players[1].pig_list[0].door_lock)
            user1_pig1_clean_or_not = str(self.players[1].pig_list[1].clean_or_not)
            user1_pig1_have_house = str(self.players[1].pig_list[1].have_house)
            user1_pig1_have_lc = str(self.players[1].pig_list[1].have_lc)
            user1_pig1_door_lock = str(self.players[1].pig_list[1].door_lock)
            user1_pig2_clean_or_not = str(self.players[1].pig_list[2].clean_or_not)
            user1_pig2_have_house = str(self.players[1].pig_list[2].have_house)
            user1_pig2_have_lc = str(self.players[1].pig_list[2].have_lc)
            user1_pig2_door_lock = str(self.players[1].pig_list[2].door_lock)
            user2_name = str(self.players[2].name)
            user2_id = str(self.players[2].id)
            user2_card0_type = self.players[2].card_list[0].card_type
            user2_card1_type = self.players[2].card_list[1].card_type
            user2_card2_type = self.players[2].card_list[2].card_type
            user2_pig0_clean_or_not = str(self.players[2].pig_list[0].clean_or_not)
            user2_pig0_have_house = str(self.players[2].pig_list[0].have_house)
            user2_pig0_have_lc = str(self.players[2].pig_list[0].have_lc)
            user2_pig0_door_lock = str(self.players[2].pig_list[0].door_lock)
            user2_pig1_clean_or_not = str(self.players[2].pig_list[1].clean_or_not)
            user2_pig1_have_house = str(self.players[2].pig_list[1].have_house)
            user2_pig1_have_lc = str(self.players[2].pig_list[1].have_lc)
            user2_pig1_door_lock = str(self.players[2].pig_list[1].door_lock)
            user2_pig2_clean_or_not = str(self.players[2].pig_list[2].clean_or_not)
            user2_pig2_have_house = str(self.players[2].pig_list[2].have_house)
            user2_pig2_have_lc = str(self.players[2].pig_list[2].have_lc)
            user2_pig2_door_lock = str(self.players[2].pig_list[2].door_lock)
            user3_name = str(self.players[3].name)
            user3_id = str(self.players[3].id)
            user3_card0_type = self.players[3].card_list[0].card_type
            user3_card1_type = self.players[3].card_list[1].card_type
            user3_card2_type = self.players[3].card_list[2].card_type
            user3_pig0_clean_or_not = str(self.players[3].pig_list[0].clean_or_not)
            user3_pig0_have_house = str(self.players[3].pig_list[0].have_house)
            user3_pig0_have_lc = str(self.players[3].pig_list[0].have_lc)
            user3_pig0_door_lock = str(self.players[3].pig_list[0].door_lock)
            user3_pig1_clean_or_not = str(self.players[3].pig_list[1].clean_or_not)
            user3_pig1_have_house = str(self.players[3].pig_list[1].have_house)
            user3_pig1_have_lc = str(self.players[3].pig_list[1].have_lc)
            user3_pig1_door_lock = str(self.players[3].pig_list[1].door_lock)
            user3_pig2_clean_or_not = str(self.players[3].pig_list[2].clean_or_not)
            user3_pig2_have_house = str(self.players[3].pig_list[2].have_house)
            user3_pig2_have_lc = str(self.players[3].pig_list[2].have_lc)
            user3_pig2_door_lock = str(self.players[3].pig_list[2].door_lock)
            user0_infrom = user0_name+" "+user0_id+" "+user0_card0_type+" "+user0_card1_type+" "+user0_card2_type+" "+user0_pig0_clean_or_not+" "+user0_pig0_have_house+" "+user0_pig0_have_lc+" "+user0_pig0_door_lock+" "+user0_pig1_clean_or_not+" "+user0_pig1_have_house+" "+user0_pig1_have_lc+" "+user0_pig1_door_lock+" "+user0_pig2_clean_or_not+" "+user0_pig2_have_house+" "+user0_pig2_have_lc+" "+user0_pig2_door_lock
            user1_infrom = user1_name+" "+user1_id+" "+user1_card0_type+" "+user1_card1_type+" "+user1_card2_type+" "+user1_pig0_clean_or_not+" "+user1_pig0_have_house+" "+user1_pig0_have_lc+" "+user1_pig0_door_lock+" "+user1_pig1_clean_or_not+" "+user1_pig1_have_house+" "+user1_pig1_have_lc+" "+user1_pig1_door_lock+" "+user1_pig2_clean_or_not+" "+user1_pig2_have_house+" "+user1_pig2_have_lc+" "+user1_pig2_door_lock
            user2_infrom = user2_name+" "+user2_id+" "+user2_card0_type+" "+user2_card1_type+" "+user2_card2_type+" "+user2_pig0_clean_or_not+" "+user2_pig0_have_house+" "+user2_pig0_have_lc+" "+user2_pig0_door_lock+" "+user2_pig1_clean_or_not+" "+user2_pig1_have_house+" "+user2_pig1_have_lc+" "+user2_pig1_door_lock+" "+user2_pig2_clean_or_not+" "+user2_pig2_have_house+" "+user2_pig2_have_lc+" "+user2_pig2_door_lock
            user3_infrom = user3_name+" "+user3_id+" "+user3_card0_type+" "+user3_card1_type+" "+user3_card2_type+" "+user3_pig0_clean_or_not+" "+user3_pig0_have_house+" "+user3_pig0_have_lc+" "+user3_pig0_door_lock+" "+user3_pig1_clean_or_not+" "+user3_pig1_have_house+" "+user3_pig1_have_lc+" "+user3_pig1_door_lock+" "+user3_pig2_clean_or_not+" "+user3_pig2_have_house+" "+user3_pig2_have_lc+" "+user3_pig2_door_lock
            start_msg = "game_start"+" "+user0_infrom+" "+user1_infrom+" "+user2_infrom+" "+user3_infrom
            self.boardcast(start_msg)
            self.state = "playing"
            print('start game')
            sleep(1)
            turn_msg = "turn"+" "+self.players[self.current_index].name
            self.boardcast(turn_msg)
        else:
            print('game is not start')

    def register_client(self, addr, client):
        try:
            if addr in self.players or self.state != 'waiting_to_start':
                return False

            raw_msglen = self.recvall(client, 4)
            if not raw_msglen:
                return None
            msglen = struct.unpack('<I', raw_msglen)[0]

            # Read the message data
            msg = self.recvall(client, msglen).decode()
            request = msg.split()[0]
            name = msg.split()[1]

            if request != 'register_request': 
                return False

            cur_id = self.create_id()
            self.players.append(Player(addr, client, name, cur_id))

            sleep(0.5)
            thread = threading.Thread(target=self.handle_client, args=(addr, client, name, cur_id))
            thread.daemon = True
            thread.start()

            sleep(1.5)
            #player join
            self.check_if_start()

            return True

        except Exception as e:
            print(e)
            return False

game = Game()
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 1234))
server.listen(4)
while True:
    client, addr = server.accept()
    print('connected by', addr)
    if not game.register_client(addr, client):
        client.close()