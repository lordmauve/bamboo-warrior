import random
from bamboo.geom import Vec2
from bamboo.actors.projectiles import Shuriken


class AIController(object):
	SLEEP_DISTANCE = 700	# Don't engage targets further away than this
	ATTACK_RATE = 50	# min number of frames between attacks

	def __init__(self, character):
		self.character = character
		self.target = None
		self.attack_timer = 0
		self.strategy = None
		self.strategy_time = 0

		self.target_tree = None

	def choose_target(self):
		"""Returns the nearest player character, or None
		if there are no players in range"""
		targets = self.character.level.find_playercharacters()
		nearest, distance = None, None
		for t in targets:
			d = self.character.distance_to(t.pos)
			if nearest is None or d < distance:
				nearest = t
				distance = d 
		if distance < self.SLEEP_DISTANCE:
			return nearest

	def range_to(self, pos):
		return (pos - self.character.pos).mag()

	def range_to_target(self):
		return self.range_to(self.target.pos)

	def direction_to(self, pos):
		x = self.character.pos.x
		tx = pos.x 
		if x < tx:
			return 'r'
		else:
			return 'l'
		# TODO: handle above or below case

	def run_towards(self, pos):
		dir = self.direction_to(pos)
		if dir == 'r':
			self.character.run_right()
		else:
			self.character.run_left()

	def run_from(self, pos):
		dir = self.direction_to(pos)
		if dir == 'l':
			self.character.run_right()
		else:
			self.character.run_left()

	def run_towards_target(self):
		if not self.target:
			return
		self.run_towards(self.target.pos)

	def run_from_target(self):
		if not self.target:
			return
		self.run_from(self.target.pos)

	def is_target_climbing(self):
		return self.target.is_climbing() and self.target.climbing_height > 2

	def on_character_death(self):
		pass

	def reconsider_target(self):
		if self.target and (self.range_to_target() > self.SLEEP_DISTANCE or not self.target.is_alive()):
			self.target = None
			self.strategy = None

		if not self.target or not self.target.is_alive():
			t = self.choose_target()
			if not t:
				return
			self.target = t

	def update(self):
		if self.attack_timer > 0:
			self.attack_timer -= 1
		self.reconsider_target()

		if not self.target:
			return

		if not self.strategy or self.strategy_time % 30 == 0:
			self.pick_strategy()

		getattr(self, 'strategy_' + self.strategy)()
		self.strategy_time += 1

	def set_strategy(self, strategy):
		self.strategy = strategy
		self.strategy_time = 1

	def pick_strategy(self):
		if random.randint(0, 5) == 0:
			self.set_strategy('treesnipe')
		elif self.target.is_climbing():
			self.set_strategy('climbtree')
		else:
			self.set_strategy('approach')

	def pick_tree(self):
		nearest = None
		distance = None
		sx = self.character.pos.x
		tx = self.target.pos.x
		for a in self.character.level.get_climbables():
			ax = a.pos.x
			if sx < tx - 100:
				if a.pos.x > tx:
					continue
			elif sx > tx + 100:
				if a.pos.x < tx:
					continue
			if a.actors:
				continue
				
			d = abs(tx - ax)
			if nearest is None or d < distance:
				nearest = a
				distance = d

		return nearest, distance

	def strategy_climbtree(self):
		"""Climb a tree near the player"""
		if self.target_tree is None or self.strategy_time % 10 == 0:
			tree, dist = self.pick_tree()
			if tree and dist < 300:
				self.target_tree = tree
			else:
				if self.character.is_climbing():
					self.character.jump()
				self.set_strategy('await')
				return

		px = self.character.pos.x
		tx = self.target_tree.pos.x

		if self.character.is_climbing() and self.character.climbing != self.target_tree:
			self.run_towards(self.target_tree.pos)
			self.character.jump()
		elif abs(px - tx) < 20:
			self.character.climb(self.target_tree, 1)
			self.set_strategy('treefight')
		else:
			self.run_towards(self.target_tree.pos)

	def strategy_treefight(self):
		"""Once in a tree, fight with the player"""
		if self.target.pos.y > self.character.pos.y + 50:
			self.character.climb_up()
		elif self.target.pos.y < self.character.pos.y - 20:
			self.character.climb_down()
			if not self.character.is_climbing():
				self.set_strategy('approach')
		else:
			self.character.looking = self.direction_to(self.target.pos)
			if (self.target.pos - self.character.pos).mag() < 200:
				self.character.attack()
			self.character.stop()
		
	def strategy_approach(self):
		"""Approach the player and fight"""
		if self.is_target_climbing() and self.strategy_time % 60 == 0:
			self.pick_strategy()
			return
		if self.range_to_target() > 300:
			self.run_towards_target()
		elif self.range_to_target < 150:
			self.run_from_target()
		else:
			self.character.dir = self.direction_to(self.target.pos)
			if self.attack_timer == 0:
				self.character.attack()
				self.attack_timer = self.ATTACK_RATE
			self.character.stop()
		if self.character.is_climbing():
			self.character.jump()

	def strategy_await(self):
		if not self.is_target_climbing():
			self.pick_strategy()
			return

		if self.range_to(self.target.climbing.pos) > 400:
			self.run_towards(self.target.climbing.pos)
			if self.character.is_climbing():
				self.character.jump()
		else:
			self.character.dir = self.direction_to(self.target.climbing.pos)
			if self.character.is_on_ground():
				self.character.crouch()
			elif self.character.is_climbing():
				self.character.jump()

	def strategy_treesnipe(self):
		"""Pick a tree to snipe from and climp onto it"""
		if self.target_tree is None or self.strategy_time % 10 == 0:
			tree, dist = self.pick_tree()
			if tree:
				self.target_tree = tree
			else:
				self.pick_strategy()
				return

		px = self.character.pos.x
		tx = self.target_tree.pos.x

		if self.character.is_climbing() and self.character.climbing != self.target_tree:
			self.run_towards(self.target_tree.pos)
			self.character.jump()
		elif abs(px - tx) < 20:
			self.character.climb(self.target_tree, 1)
			self.set_strategy('treesniping')
		else:
			self.run_towards(self.target_tree.pos)

	def strategy_treesniping(self):
		if not self.character.is_climbing():
			self.pick_strategy()
			return
		
		alt = self.character.pos.y - self.character.ground_level()
		if alt < 400:
			self.character.climb_up()
		elif self.character.can_attack():
			self.character.throw_projectile(self.target.pos + Vec2(0, 80), Shuriken)
			self.set_strategy('treefight')
