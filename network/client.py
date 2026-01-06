#!/usr/bin/env python3

import pygame
import socket
import time
import argparse
import copy
from signal import signal, SIGINT
from typing import Optional, cast
import random

from twnet_parser.messages7.game.sv_client_info import MsgSvClientInfo
from twnet_parser.messages7.system.input import MsgInput
from twnet_parser.messages7.system.snap import MsgSnap
from twnet_parser.messages7.system.snap_empty import MsgSnapEmpty
from twnet_parser.messages7.system.snap_single import MsgSnapSingle
from twnet_parser.net_message import NetMessage
from twnet_parser.packer import Unpacker
from twnet_parser.packet import TwPacket7, parse7
from twnet_parser.messages7.control.token import CtrlToken
from twnet_parser.messages7.control.connect import CtrlConnect
from twnet_parser.messages7.control.close import CtrlClose
from twnet_parser.messages7.system.info import MsgInfo
from twnet_parser.messages7.system.map_change import MsgMapChange
from twnet_parser.messages7.system.ready import MsgReady
from twnet_parser.messages7.game.cl_start_info import MsgClStartInfo
from twnet_parser.messages7.system.enter_game import MsgEnterGame
from twnet_parser.snap7.player_input import ObjPlayerInput

from twnet_parser.constants import NET_MAX_PACKETSIZE, NET_MAX_SEQUENCE
from twnet_parser.session import seq_in_backroom
from twnet_parser.session7 import Session7
from twnet_parser.snap7.character import ObjCharacter
from twnet_parser.snapshot import Snapshot
from twnet_parser.snapshot_storage import SnapshotStorage

example_text = '''example:
 python %(prog)s localhost 8303'''

description_text = '''
 Connects to given server. And keeps the connection alive.
'''

class TeeworldsClient():
    def __init__(self, host, port):
        self.sock = None
        self.connected = False
        self.connect(host, port)

    def connect(self, host, port):
        self.connected = False
        self.host = host
        self.port = port
        self.dest_srv = (self.host, self.port)

        self.log(f"Connecting to {host}:{port} ...")

        if self.sock:
            self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))

        self.outfile = None
        self.downloaded_chunks = 0
        self.downloaded_bytes = 0
        self.session = Session7()
        self.snap_storage = SnapshotStorage()
        self.input = MsgInput()
        self.map_info: Optional[MsgMapChange] = None
        self.my_token = b'\xff\xaa\xbb\xee'
        self.srv_token = b'\xff\xff\xff\xff'
        self.last_send_time = time.time()
        self.current_snapshot = Snapshot(version='0.7')
        self.local_client_id = -1
        self.characters: dict[int, ObjCharacter] = {}

        # TODO: we should be able to set this
        # ctrl_token = CtrlToken(we_are_a_client = True)
        ctrl_token = CtrlToken()
        ctrl_token.response_token = self.my_token
        self.send_msg(ctrl_token)

    def disconnect(self):
        close = CtrlClose()
        self.log("sending disconnect")
        self.send_msg(close)

    def log(self, message):
        print(f"[client] {message}")

    def send_input(self):
        self.send_msg(self.input)

    def send_msg(self, messages):
        if self.sock is None:
            self.log("failed to send message! No socket!")
            return

        if not isinstance(messages, list):
            messages = [messages]
        packet = TwPacket7()
        packet.header.token = self.srv_token
        for msg in messages:
            if hasattr(msg, 'header'):
                if msg.header.flags.vital:
                    self.session.sequence += 1
                msg.header.seq = self.session.sequence
            packet.messages.append(msg)
        self.last_send_time = time.time()
        packet.header.ack = self.session.ack
        self.sock.sendto(packet.pack(), self.dest_srv)

    def on_snapshot(self, snapshot: Snapshot):
        self.current_snapshot = snapshot
        self.characters = {}
        for item in self.current_snapshot.items:
            if item.item_name != 'obj.character':
                continue
            char = cast(ObjCharacter, item)
            self.characters[item.id] = char

    def tick(self):
        if self.sock is None:
            self.log("You have to call connect() before you can tick()")
            return
        data, _ = self.sock.recvfrom(NET_MAX_PACKETSIZE)
        packet = parse7(data)

        for msg in packet.messages:
            if hasattr(msg, 'header'):
                msg = cast(NetMessage, msg)
                if msg.header.flags.vital:
                    if msg.header.seq == (self.session.ack + 1) % NET_MAX_SEQUENCE:
                        # in sequence
                        self.session.ack = (self.session.ack + 1) % NET_MAX_SEQUENCE
                    else:
                        # old packet that we already got
                        if seq_in_backroom(msg.header.seq, self.session.ack):
                            continue
                        # out of sequence, request resend
                        self.log("need to request resend, but that is not implemented yet!")

            if msg.message_name.startswith('snap_') and not self.connected:
                self.connected = True
                self.log("connected!")

            if msg.message_name == 'token':
                msg = cast(CtrlToken, msg)
                self.srv_token = msg.response_token

                ctrl_connect = CtrlConnect()
                ctrl_connect.response_token = self.my_token
                self.send_msg(ctrl_connect)
            elif msg.message_name == 'accept':
                info = MsgInfo()
                info.header.flags.vital = True
                self.send_msg(info)
            elif msg.message_name == 'map_change' or msg.message_name == 'map_data':
                ready = MsgReady()
                ready.header.flags.vital = True
                self.send_msg(ready)
            elif msg.message_name == 'sv_client_info':
                msg = cast(MsgSvClientInfo, msg)
                if msg.local:
                    self.local_client_id = msg.client_id
            elif msg.message_name == 'con_ready':
                self.log("sending info")
                startinfo = MsgClStartInfo()
                startinfo.header.flags.vital = True
                self.send_msg(startinfo)
                enter_game = MsgEnterGame()
                enter_game.header.flags.vital = True
                self.send_msg(enter_game)
            elif msg.message_name == 'close':
                msg = cast(CtrlClose, msg)
                self.log(f"disconnected reason='{msg.reason}'")
                exit(1)
            elif msg.message_name == 'snap_single':
                msg = cast(MsgSnapSingle, msg)
                delta_tick = msg.tick - msg.delta_tick

                # # TODO: this comparison looks wrong to me but its the same in teeworlds-go
                # if self.snap_storage.current_recv_tick < msg.tick:
                #     self.log(f"dropping snap with too old game tick msg.tick={msg.tick} current_recv_tick={self.snap_storage.current_recv_tick}")
                #     continue

                if msg.tick != self.snap_storage.current_recv_tick:
                    self.snap_storage.snapshot_parts = 0
                    self.snap_storage.current_recv_tick = msg.tick

                # empty snap if delta is -1
                prev_snap = Snapshot(version='0.7')

                if delta_tick != -1:
                    prev_snap = self.snap_storage.get(delta_tick)

                if not prev_snap:
                    raise ValueError(f"delta snapshot with tick {delta_tick} not found")

                unpacker = Unpacker(msg.data)
                new_full_snap = prev_snap.unpack_delta(unpacker)
                self.snap_storage.add(msg.tick, new_full_snap)
                self.snap_storage.purge_until(delta_tick)

                self.on_snapshot(new_full_snap)

                self.input.ack_snapshot = msg.tick
                self.input.intended_tick = self.snap_storage.newest_tick
                self.snap_storage.current_recv_tick = msg.tick

                # TODO: should we send input here? teeworlds-go/protocol does it

            elif msg.message_name == 'snap_empty':
                msg = cast(MsgSnapEmpty, msg)
                delta_tick = msg.tick - msg.delta_tick
                # self.log(f"got snap empty with tick={msg.tick} delta_tick={delta_tick}")

                # # TODO: this comparison looks wrong to me but its the same in teeworlds-go
                # if self.snap_storage.current_recv_tick < msg.tick:
                #     self.log(f"dropping snap with too old game tick msg.tick={msg.tick} current_recv_tick={self.snap_storage.current_recv_tick}")
                #     continue

                if msg.tick != self.snap_storage.current_recv_tick:
                    self.snap_storage.snapshot_parts = 0
                    self.snap_storage.current_recv_tick = msg.tick

                # empty snap if delta is -1
                prev_snap = Snapshot(version='0.7')

                if delta_tick != -1:
                    prev_snap = self.snap_storage.get(delta_tick)

                if not prev_snap:
                    raise ValueError(f"delta snapshot with tick {delta_tick} not found")

                # TODO: the deepcopy can probably be avoided
                #       if we correctly drop or purge unused snaps
                self.snap_storage.add(msg.tick, copy.deepcopy(prev_snap))
                self.snap_storage.purge_until(delta_tick)

                self.on_snapshot(prev_snap)

                self.input.ack_snapshot = msg.tick
                self.input.intended_tick = self.snap_storage.newest_tick
                self.snap_storage.current_recv_tick = msg.tick
            elif msg.message_name == 'snap':
                msg = cast(MsgSnap, msg)
                delta_tick = msg.tick - msg.delta_tick

                # TODO: this comparison looks wrong to me but its the same in teeworlds-go
                if self.snap_storage.current_recv_tick < msg.tick:
                    self.log(f"dropping snap with too old game tick msg.tick={msg.tick} current_recv_tick={self.snap_storage.current_recv_tick}")
                    continue

                if msg.tick != self.snap_storage.current_recv_tick:
                    self.snap_storage.snapshot_parts = 0
                    self.snap_storage.current_recv_tick = msg.tick

                self.snap_storage.add_incoming_data(msg.part, msg.num_parts, msg.data)

                self.snap_storage.snapshot_parts |= 1 << msg.part

                if msg.part != msg.num_parts -1:
                    # TODO: remove this if it works
                    self.log(f"storing partial snap part={msg.part} num_parts={msg.num_parts}")
                    continue

                if self.snap_storage.snapshot_parts != msg.num_parts - 1:
                    self.log(f"got last part but mussing previous parts part={msg.part} num_parts={msg.num_parts}")
                    continue

                self.snap_storage.snapshot_parts = 0

                # empty snap if delta is -1
                prev_snap = Snapshot(version='0.7')

                if delta_tick != -1:
                    prev_snap = self.snap_storage.get(delta_tick)

                if not prev_snap:
                    raise ValueError(f"delta snapshot with tick {delta_tick} not found")

                unpacker = Unpacker(self.snap_storage.incoming_data())
                new_full_snap = prev_snap.unpack_delta(unpacker)
                self.snap_storage.add(msg.tick, new_full_snap)
                self.snap_storage.purge_until(delta_tick)

                self.on_snapshot(new_full_snap)

                self.input.ack_snapshot = msg.tick
                self.input.intended_tick = self.snap_storage.newest_tick
                self.snap_storage.current_recv_tick = msg.tick

        if (time.time() - self.last_send_time) > 1:
            # self.input.input = ObjPlayerInput()
            # generate some random inputs for testing
            # self.input.input_size = 40
            # self.input.input.direction = random.randint(-1, 1)
            # self.input.input.fire = random.randint(0, 100)
            # self.input.input.hook = random.randint(0, 1) == 0
            # self.input.input.jump = random.randint(0, 1) == 0
            # self.input.input.target_x = random.randint(-200, 200)
            # self.input.input.target_y = random.randint(-200, 200)
            self.send_input()

    def center_around_tee(self, tee: ObjCharacter) -> pygame.Vector2:
        wc = screen.get_width() / 2
        hc = screen.get_height() / 2
        x = -tee.x + wc
        y = -tee.y + hc
        return pygame.Vector2(x, y)

    def render(self):
        if self.local_client_id == -1:
            return

        if self.local_client_id not in self.characters:
            print("TODO: being dead is not supported yet")
            return

        own_tee = self.characters[self.local_client_id]
        offset = self.center_around_tee(own_tee)

        for _, char in self.characters.items():
            print(f"cid={char.id} at x={char.x / 32} y={char.y / 32}")
            player_pos = pygame.Vector2(char.x + offset.x, char.y + offset.y)
            pygame.draw.circle(screen, "red", player_pos, 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='snap_printer.py',
        description=description_text,
        epilog=example_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    args = parser.parse_args()
    
    client = TeeworldsClient(host = args.host, port = args.port)

    def handler(signal_received, _):
        global client
        print(f"got signal: {signal_received}")
        print('SIGINT or CTRL-C detected. Exiting gracefully')
        client.disconnect()
        exit(0)

    signal(SIGINT, handler)

    pygame.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        client.tick()
        screen.fill("purple")
        client.render()

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
