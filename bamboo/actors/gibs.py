import random
from bamboo.actors.base import PhysicalObject


class BloodSpray(PhysicalObject):
	initial_animation = 'spray'
	MASS = 0.2

	def __init__(self, v):
		super(BloodSpray, self).__init__()
		self.v = v
		self.dir = 'r' if v.x > 0 else 'l'
	
	def on_spawn(self):
		anim = random.choice(['spray-1', 'spray-2', 'spray-3']) 
		self.play_animation(anim, directional=True)

	@classmethod
	def on_class_load(cls):
		cls.load_directional_sprite('spray-1', 'blood-spray-1.png', anchor_x=0, anchor_y='center')
		cls.load_directional_sprite('spray-2', 'blood-spray-2.png', anchor_x=0, anchor_y='center')
		cls.load_directional_sprite('spray-3', 'blood-spray-3.png', anchor_x=0, anchor_y='center')

	def update(self):
		if self.is_on_ground():
			self.level.kill(self)
		else:
			super(BloodSpray, self).update()
		if self.dir == 'r':
			self.rotation = -self.v.angle_in_degrees()
		else:
			self.rotation = 180 - self.v.angle_in_degrees()
