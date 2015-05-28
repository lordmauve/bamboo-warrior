from bamboo.actors.characters import Character, Corpse


class NinjaCorpse(Corpse):
	@classmethod
	def on_class_load(cls):
		cls.load_directional_sprite('dying', 'ninja-dying.png', anchor_x='right')
		cls.load_directional_sprite('dead', 'ninja-dead.png', anchor_x='right', anchor_y=10)


class Ninja(Character):
	"""Represents a set of graphics"""
	TRAIL_LENGTH = 2
	TRAIL_DECAY = 0.7

	MAX_HEALTH = 10

	CORPSE = NinjaCorpse
	
	@classmethod
	def on_class_load(cls):
		cls.load_directional_sprite('standing', anchor_x=30)
		cls.load_directional_sprite('attacking', anchor_x=30)
		cls.load_directional_sprite('crouching', anchor_x=30)
		cls.load_directional_sprite('crouching-attacking', anchor_x=30)
		cls.load_directional_sprite('jumping', anchor_x=50, anchor_y=20)
		cls.load_directional_sprite('falling', anchor_x=40, anchor_y=20)
		cls.load_directional_sprite('clinging', anchor_x=72)
		cls.load_directional_sprite('clinging-lookingout', anchor_x=72)
		cls.load_directional_sprite('clinging-lookingacross', anchor_x=35)
		cls.load_directional_sprite('clinging-slidingdown', anchor_x=51)
		cls.load_directional_sprite('clinging-lookingout-attacking', anchor_x=241)
		cls.load_directional_sprite('clinging-lookingacross-attacking', anchor_x=35)


		cls.load_animation('running', 'ninja-running%d.png', 6, anchor_x=105)
		cls.load_animation('climbing', 'ninja-climbing%d.png', 5, anchor_x=60)

	def update_animation(self):
		if self.is_attacking():
			if self.is_climbing():
				if self.looking != self.dir:
					self.play_animation('clinging-lookingout-attacking')
				else:
					self.play_animation('clinging-lookingacross-attacking')
			elif self.crouching:
				self.play_animation('crouching-attacking')
			else:
				self.play_animation('attacking')
		elif not self.is_climbing():
			if self.crouching:
				self.play_animation('crouching')
			elif self.is_on_ground():
				if self.v.mag() < 0.01:
					self.play_animation('standing')
				else:
					self.play_animation('running')
			else:
				if self.v.y <= self.FALL_SPEED:
					self.play_animation('falling')
		else:
			if self.climb_rate > 0:
				self.play_animation('climbing')
			elif self.climb_rate < 0:
				self.play_animation('clinging-slidingdown')
			else:
				if self.looking is None:
					self.play_animation('clinging')
				elif self.looking != self.dir:
					self.play_animation('clinging-lookingout')
				else:
					self.play_animation('clinging-lookingacross')

	def on_spawn(self):
		self.health = self.MAX_HEALTH
		self.play_animation('standing')

	def on_jump(self):
		#self.play_sound('jumping')
		self.play_animation('jumping')
