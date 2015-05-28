from bamboo.actors.base import PhysicalObject

class Shuriken(PhysicalObject):
	MASS = 0.1

	layer = 3

	def __init__(self, v, owner):
		super(Shuriken, self).__init__()
		self.owner = owner
		self.v = v
		self.spin = 30
		self.rest_time = 0
	
	def on_spawn(self):
		self.play_animation('shuriken')

	@classmethod
	def on_class_load(cls):
		cls.load_sprite('shuriken', 'shuriken.png', anchor_x='center', anchor_y='center')

	def on_collide(self, actor):
		if actor == self.owner:
			return
		elif isinstance(actor, Character):
			actor.hit(self.v * self.MASS, 10)

	def update(self):
		if self.rest_time >= 100:
			self.level.kill(self)
		else:
			super(Shuriken, self).update()
		
		if not self.v:
			self.rest_time += 1

		self.rotation += self.spin
