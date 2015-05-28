import pyglet

from bamboo.resources import ResourceTracker
from bamboo.geom import Vec2

class Actor(ResourceTracker):
	initial_animation = None
	current = None
	next = None	# sprite to change to at next frame
	sprite = None

	controller = None
	collision_mask = 0x00

	level = None
	rotation = 0
	scale = 1.0
	opacity = 255

	dir = 'r'

	def _get_pos(self):
		return self._pos
	
	def _set_pos(self, pos):
		self._pos = pos
		if self.level:
			# TODO: tell level we've moved, so level can optimise
			self._ground_level = self.level.ground.height_at(pos.x)
			self._ground_normal = self.level.ground.normal_at(pos.x)

	_pos = Vec2(0, 0)
	pos = property(_get_pos, _set_pos)

	def add_death_listener(self, callback):
		try:
			self.death_listeners.add(callback)
		except AttributeError:
			self.death_listeners = set([callback])

	def remove_death_listener(self, callback):
		try:
			self.death_listeners.remove(callback)
		except AttributeError, KeyError:
			pass

	def fire_death_event(self):
		if hasattr(self, 'death_listeners'):
			for l in self.death_listeners:
				l(self)

	def is_alive(self):
		return self.level is not None

	def die(self):
		self.fire_death_event()
		self.level.kill(self)

	def distance_to(self, pos):
		return (pos - self.pos).mag()

	def ground_level(self):
		try:
			return self._ground_level
		except AttributeError:
			self._ground_level = self.level.ground.height_at(self.pos.x)
			return self._ground_level

	def ground_normal(self):
		try:
			return self._ground_normal
		except AttributeError:
			self._ground_normal = self.level.ground.normal_at(self.pos.x)
			return self._ground_normal
			

	def play_sound(self, name):
		"""Play a named sound from the Actor's resources"""
		self.sounds[name].play()

	def play_animation(self, name, directional=False):
		"""Set the current animation""" 
		if directional:
			name = name + '-' + self.dir
		if self.current == name:
			return
		self.next = name

	def parent_group(self):
		if hasattr(self, 'layer'):
			return pyglet.graphics.OrderedGroup(self.layer)

	def update_batch(self, batch):
		if self.next is not None:
			group = self.parent_group()
			if not self.sprite:
				self.sprite = pyglet.sprite.Sprite(self.graphics[self.next], self.pos.x, self.pos.y, batch=batch, group=group)
				self.sprite.opacity = self.opacity
				self.sprite._scale = self.scale
				self.sprite._update_position()
			self.sprite.image = self.graphics[self.next]
			self.current = self.next
			self.next = None
		elif self.sprite: 
			# pyglet regenerates the position whenever any property is set
			# accessing the internal properties directly, and then updating, is faster
			self.sprite._rotation = self.rotation
			self.sprite._x = self.pos.x
			self.sprite._y = self.pos.y
			self.sprite._scale = self.scale
			self.sprite._update_position()
			self.sprite.opacity = self.opacity

	def delete(self):
		"""Remove from batch"""
		if self.sprite:
			self.sprite.delete()
			self.sprite = None

	def update(self):
		"""Subclasses can implement this method if necessary to implement game logic"""

	def on_spawn(self):
		"""Subclasses can implement this method to initialise the actor"""
		if self.initial_animation:
			self.play_animation(self.initial_animation)


GRAVITY = Vec2(0, -2.3)

class PhysicalObject(Actor):
	"""A PhysicalObject is an actor bound by simple platform physics"""
	MASS = 15
	FRICTION = 0.6
	LINEAR_DAMPING = 0.0

	def __init__(self, pos=Vec2(0,0)):
		self.pos = Vec2(0, 0)
		self.v = Vec2(0, 0)
		self.f = self.get_weight()
		self.runforce = 0
	
	def apply_force(self, vec):
		self.f += vec

	def apply_impulse(self, vec):
		self.v += vec

	def apply_ground_force(self):
		normal = self.ground_normal()
		tangent = normal.perpendicular()

		restitution = -min(normal.dot(self.v), 0) * normal
		self.apply_impulse(restitution)

		normalforce = -min(normal.dot(self.f), 0) * normal
		self.apply_force(normalforce)
	
		self.runforce = normalforce.mag() / self.get_weight().mag()

		friction = self.FRICTION * normalforce.mag()	# max friction
		ground_velocity = tangent.component_of(self.v)
		ground_force = tangent.component_of(self.f)
		if ground_velocity:
			f = min(friction, ground_velocity.mag() * self.MASS + ground_force.mag())
			self.apply_force(-ground_velocity.normalized() * f)
		elif ground_force:
			f = min(ground_force.mag(), friction)
			self.apply_force(-ground_force.normalized() * f)

	def is_on_ground(self):
		return self.pos.y <= (self.ground_level() + 0.5)

	def get_net_force(self):
		"""This can only be called once per frame"""
		if self.is_on_ground():
			self.apply_ground_force()
		f = self.f
		self.f = self.get_weight()
		return f

	def get_weight(self):
		return GRAVITY * self.MASS

	def update(self):
		f = self.get_net_force()
		accel = f / self.MASS

		g = self.ground_level()
		if self.pos.y < g:
			self.pos -= self.ground_normal().component_of(Vec2(0, self.pos.y - g))

		self.v = (self.v + accel) * (1 - self.LINEAR_DAMPING)
		self.pos += self.v
