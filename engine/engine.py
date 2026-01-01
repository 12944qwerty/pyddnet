from engine.constants import *
from engine.maploader import MapLoader
from engine.tee import Tee

class DDNetPhysicsEngine:
    def __init__(
        self,
        map: MapLoader,
        players: list[Tee]
    ):
        self.map = map
        self.players = players
        self.accumulated_time = 0.0
        
    def update(self, dt):
        STEP_TIME = 1/50
        self.accumulated_time += dt
        while self.accumulated_time >= STEP_TIME:
            self.tick(STEP_TIME)
            self.accumulated_time -= STEP_TIME
        
    def tick(self, dt):
        for player in self.players:
            player.tick(dt, self.map)
            
            player.move(dt, self.map)