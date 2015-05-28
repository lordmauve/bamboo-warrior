class PlayerController(object):
	"""A PlayerController is a controller for a Character
	that responds to keyboard input"""

	def __init__(self, character):
		self.character = character
		self.character.is_pc = True
		self.active = False
		self.attack_timer = None

	def right(self):
		self.character.run_right()
		self.active = True

	def left(self):
		self.character.run_left()
		self.active = True

	def up(self):
		if self.character.is_climbing():
			self.character.climb_up()
		else:
			tree = self.character.nearby_climbable()
			if not tree:
				return
			self.character.climb(tree, 1)
		# else look up?
		self.active = True

	def down(self):
		if self.character.is_climbing():
			self.character.climb_down()
		elif self.character.is_on_ground():
			self.character.crouch()
		else:
			tree = self.character.nearby_climbable()
			if not tree:
				return
			self.character.climb(tree, -1)
		self.active = True

	def jump(self):
		self.character.jump()
		self.active = True

	def attack(self):
		self.character.attack()

	def on_character_death(self):
		pass

	def update(self):
		if not self.active:
			self.character.stop()
		self.active = False
