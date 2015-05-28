import random
from bamboo.geom import Vec2

from base import Actor

class Torii(Actor):
	initial_animation = 'torii'
	layer = 0
	@classmethod
	def on_class_load(cls):
		cls.load_sprite('torii', 'torii.png')


class EatingSamurai(Actor):
	initial_animation = 'eating'
	layer = 2

	@classmethod
	def on_class_load(cls):
		cls.load_sprite('eating', 'samurai-eating.png')


class Campfire(Actor):
	initial_animation = 'campfire-r'
	layer = 2

	@classmethod
	def on_class_load(cls):
		cls.load_animation('campfire', 'campfire%d.png', 4)

	def update(self):
		from bamboo.actors.particles import Smoke
		if random.randint(0, 10) == 0:
			v = Vec2(random.random() * 2 - 1, random.random() * 2) 
			s = Smoke(v)
			s.scale = 0.1
			self.level.spawn(s, x=self.pos.x + random.random() * 20 - 10, y=self.pos.y + 40)
