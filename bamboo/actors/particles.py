import random

from bamboo.geom import Vec2
from bamboo.actors.base import Actor


class Smoke(Actor):
	layer = 6	

	GRAVITY = Vec2(0, 0.5)

	def __init__(self, v=Vec2(0, 0), dir=None):
		super(Smoke, self).__init__()
		if dir is None:
			self.dir = random.choice(['l', 'r'])
		else:
			self.dir = dir

		self.v = v
		self.scale = 0.3 + random.random() * 0.4
		self.time = 0
		self.lifetime = 30 + int(random.random() * 30)

		self.spin = 30 if self.dir == 'l' else -30
	
	def on_spawn(self):
		self.play_animation('smoke', directional=True)

	@classmethod
	def on_class_load(cls):
		cls.load_directional_sprite('smoke', 'smoke.png', anchor_x='center', anchor_y='center')

	def update(self):
		self.time += 1
		if self.time >= self.lifetime:
			self.die()

		self.v = (self.v + Smoke.GRAVITY) * 0.9
		self.pos += self.v
		self.rotation += self.spin
		self.scale += 0.02
		self.opacity = 255 - (self.time / float(self.lifetime)) * 255


def create_puff_of_smoke(rect, level):
	import random
	c = rect.center()
	for i in range(10):
		x = random.gauss(c.x, rect.w/3)
		y = random.gauss(c.y, rect.h/3)
		v = (Vec2(x, y) - c) * 0.05
		s = Smoke(v)
		level.spawn(s, x=x, y=y)
