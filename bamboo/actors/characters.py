import pyglet
import random

from base import PhysicalObject, Actor
from bamboo.geom import Vec2, Rect

from bamboo.actors.particles import Smoke
from bamboo.actors.gibs import BloodSpray
from bamboo.actors.projectiles import Shuriken


class Character(PhysicalObject):
	"""A character is a humanoid, who can fight, climb trees, etc."""
	FALL_SPEED = -20		#threshold at which to play falling animation
	AIR_ACCEL = Vec2(5, 0)
	GROUND_ACCEL = 15
	MAX_RUN_SPEED = 20
	JUMP_IMPULSE = Vec2(0, 30)
	TREE_JUMP_IMPULSE = Vec2(10, 15)	# rightwards, negate x component for leftwards
	CLIMB_UP_RATE = 10.0
	CLIMB_DOWN_RATE = 20.0

	ATTACK_RATE = 20	# min number of frames allowed between attacks

	TRAIL_LENGTH = 10	# length of the trail
	TRAIL_DECAY = 0.9	# fractional opacity change per trail sprite

	is_pc = False	# True if this character is a player character

	collision_mask = 0x01

	layer = 5

	MAX_HEALTH = 10
	MASS = 10

	def __init__(self):
		super(Character, self).__init__()
		self.dir = 'r'
		self.rotation = 0
		self.current = None

		self.looking = None		# only used when climbing trees
		self.crouching = False
		self.climbing = None
		self.attack_timer = 0
		self.climb_rate = 0		# current climb rate (when climbing a tree)
		self.health = self.MAX_HEALTH

		self.trail = []

	def run_speed(self):
		return max(self.MAX_RUN_SPEED - self.v.mag(), 0) * self.GROUND_ACCEL

	def run_right(self):
		if self.is_climbing():
			self.apply_force(Vec2(10, 0))
			self.looking = 'r'
			self.climb_rate = 0
		else:
			self.dir = 'r'
			if self.is_on_ground():
				self.apply_force(-self.run_speed() * self.runforce * self.ground_normal().perpendicular())
			else:
				self.apply_force(self.AIR_ACCEL)
			self.crouching = False

	def run_left(self):
		if self.is_climbing():
			self.apply_force(Vec2(-10, 0))
			self.looking = 'l'
			self.climb_rate = 0
		else:
			self.dir = 'l'
			if self.is_on_ground():
				self.apply_force(self.run_speed() * self.ground_normal().perpendicular())
			else:
				self.apply_force(-self.AIR_ACCEL)
			self.crouching = False

	def is_climbing(self):
		return self.climbing is not None

	def climb(self, tree, rate=0):
		"""Set this character as climbing the given tree."""
		if self.climbing:
			self.climbing.remove_actor(self)
		tree.add_actor(self)
		self.looking = None
		self.climb_rate = rate

	def nearby_climbable(self):
		"""Returns the nearest climbable, or None if there is none
		in "range"."""
		tree, distance = self.level.get_nearest_climbable(self.pos)
		if tree and distance < 30:
			return tree

	def climb_up(self):
		assert self.is_climbing()
		self.climbing.climb_up(self, dist=self.CLIMB_UP_RATE)
		self.climb_rate = self.CLIMB_UP_RATE

	def climb_down(self):
		assert self.is_climbing()
		self.climbing.climb_down(self, dist=self.CLIMB_DOWN_RATE)
		self.climb_rate = -self.CLIMB_DOWN_RATE

	def crouch(self):
		assert self.is_on_ground()
		self.crouching = True

	def stop(self):
		if self.is_climbing():
			self.climb_rate = 0
			self.looking = None
		else:
			self.crouching = False

	def on_jump(self):
		pass

	def on_tree_jump(self):
		self.on_jump()

	def on_spawn(self):
		self.health = self.MAX_HEALTH

	def jump(self):
		if self.is_on_ground():
			self.crouching = False
			self.apply_impulse(self.JUMP_IMPULSE)
			self.on_jump()
		elif self.is_climbing():
			self.climbing.remove_actor(self)
			if self.looking:
				self.dir = self.looking
			if self.looking == 'r':
				self.apply_impulse(self.TREE_JUMP_IMPULSE)
			elif self.looking == 'l':
				ix, iy = self.TREE_JUMP_IMPULSE
				self.apply_impulse(Vec2(-ix, iy))
			self.on_tree_jump()

	def play_animation(self, name, directional=True):
		"""Set the current animation""" 
		if directional:
			name = name + '-' + self.dir
		super(Character, self).play_animation(name)

	def update_animation(self):
		pass

	def update(self):
		if self.attack_timer > 0:
			self.attack_timer -= 1

		if not self.is_climbing():
			# update physics
			super(Character, self).update()
			self.rotation = 0
		else:
			f = self.get_net_force()
			# TODO: apply force to the tree we're climbing

		if self.is_on_ground() and self.crouching and abs(self.v.x) > 2:
			if random.randint(0, 3) == 0:
				s = Smoke(dir='r' if self.dir == 'l' else 'l')
				self.level.spawn(s, x=self.pos.x)
		self.update_animation()

	def draw_trail(self):
		if not hasattr(self, 'trail_batch'):
			self.trail_batch = pyglet.graphics.Batch()

		for s in reversed(self.trail):
			s.opacity *= self.TRAIL_DECAY
		
		# copy sprite
		s = pyglet.sprite.Sprite(self.sprite.image, self.sprite.x, self.sprite.y, batch=self.trail_batch)
		s.rotation = self.sprite.rotation
		s.opacity = 128
		
		# update trail
		for f in self.trail[self.TRAIL_LENGTH - 1:]:
			f.delete()
		self.trail = [s] + self.trail[:self.TRAIL_LENGTH - 1]

		self.trail_batch.draw()

	def is_running(self):
		return self.is_on_ground() and self.v.mag() > 1

	def is_attacking(self):
		return self.attack_timer > self.ATTACK_RATE

	def can_attack(self):
		return self.attack_timer == 0

	def attack(self):
		if not self.can_attack():
			return

		self.attack_timer = self.ATTACK_RATE + 6

		off = 0
		if self.is_climbing():
			if self.dir == 'r':
				off = -30
			else:
				off = +30
			if self.dir != self.looking:
				off *= 1.2
			c = self.pos + Vec2(off, 60)
		elif self.crouching:
			c = self.pos + Vec2(off, 72)
		else:
			c = self.pos + Vec2(off, 100)

		dir = self.looking or self.dir
		if dir == 'r':
			attack_region = Rect.from_corners(c - Vec2(0, 15), c + Vec2(180, 25))
			force = Vec2(50, 0) + self.v
		else:
			attack_region = Rect.from_corners(c - Vec2(0, 15), c + Vec2(-180, 25))
			force = Vec2(-50, 0) + self.v

		victims = [a for a in self.level.characters_colliding(attack_region) if a != self]
		if not victims:
			return
		damage = 10.0 / len(victims)
		force = force / len(victims)
		for a in victims: 
			point = attack_region.intersection(a.bounds()).center()
			a.hit(point, force, damage)

	def delete(self):
		super(Character, self).delete()
		if self.climbing:
			self.climbing.remove_actor(self)

	def dims(self):
		if self.is_running():
			return 76, 130
		elif self.is_climbing():
			if self.looking == self.dir:
				return 50, 130
			else:
				return 80, 130
		elif not self.is_on_ground():
			return 80, 130
		else:
			return 60, 150

	def bounds(self):
		if self.is_climbing():
			w, h = self.dims()
			if self.looking == self.dir:
				off = 0
			else:
				if self.dir == 'r':
					off = -40
				else:
					off = +40
			return Rect(self.pos.x - w / 2 + off, self.pos.y, w, h)
		else:
			w, h = self.dims()
			return Rect(self.pos.x - w / 2, self.pos.y, w, h)

	def create_corpse(self):
		corpse = self.CORPSE(self)
		self.level.spawn(corpse, x=self.pos.x, y=self.pos.y)
		corpse.v = self.v

	def hit(self, point, force, damage=10):
		for s in range(4):
			off = Vec2(random.random() * 20 - 10, random.random() * 10 - 5) 
			self.level.spawn(BloodSpray(v=force + off), x=point.x, y=point.y)
		if not self.is_climbing():
			self.apply_impulse(force / self.MASS)
		self.health -= damage
		if self.health <= 0:
			self.create_corpse()
			self.on_death() 
			self.die()

	def throw_projectile(self, target, kls):
		if not self.can_attack():
			return
		start = self.pos + Vec2(0, 80)
		v = target - start
		if not v:
			return
		v += Vec2(0, (0.02 * v.x) ** 2) # aim above
		v = v.normalized() * 30
		self.level.spawn(kls(v, self), x=start.x, y=start.y)

	def on_death(self):
		pass

	def draw(self):
		if self.TRAIL_LENGTH:
			self.draw_trail()
		super(Character, self).draw()


class Corpse(PhysicalObject):
	def __init__(self, character):
		super(Corpse, self).__init__()
		self.dir = character.dir

	def on_spawn(self):
		self.play_animation('dying', directional=True)
		self.death_timer = 0

	def update(self):
		if self.death_timer < 200:
			super(Corpse, self).update()
		self.death_timer += 1
		if self.death_timer < 15:
			rot = 1 if self.dir == 'l' else -1
			self.rotation = min(50, self.rotation + 2 + 0.5 * rot * self.death_timer)
		elif self.death_timer == 15:
			self.rotation = 0
			self.play_animation('dead', directional=True)
		elif self.death_timer == 350:
			self.level.kill(self)
		elif self.death_timer > 200:
			self.pos += Vec2(0,-0.5)


