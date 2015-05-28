from bamboo.geom import Vec2

class ActorSpawn(object):
	NAME_MAP = {
		'BambooTree': 'bamboo.actors.trees.BambooTree',
		'Torii': 'bamboo.actors.scenery.Torii',
		'EatingSamurai': 'bamboo.actors.scenery.EatingSamurai',
		'Campfire': 'bamboo.actors.scenery.Campfire',
		'StandingNinja': 'bamboo.actors.ninja.Ninja',
	}

	def __init__(self, name, pos):
		if name not in self.NAME_MAP:
			raise ValueError("Unknown object")
		self.name = name
		self.pos = pos

	def get_class(self):
		modpath = self.NAME_MAP[self.name]
		parts = modpath.split('.')
		classname = parts[-1]
		modname = '.'.join(parts[:-1])
		mod = __import__(modname, {}, {}, [classname])
		return getattr(mod, classname)
		
	def spawn(self, level):
		from bamboo.actors.characters import Character
		from bamboo.actors.aicontroller import AIController
		obj = self.get_class()()
		if isinstance(obj, Character):
			controller = AIController(obj)
		else:
			controller = None
		level.spawn(obj, self.pos.x, self.pos.y, controller)


class Level(object):
	def __init__(self, width, height, ground, actor_spawns=[]):
		self.width = width
		self.height = height
		self.ground = ground
		self.actor_spawns = actor_spawns
		self.actors = []
		self.climbables = []
		self.characters = []
		self.controllers = []

	def restart(self):
		self.actors = []
		for spawnpoint in self.actor_spawns:
			spawnpoint.spawn(self)
			
	def spawn(self, actor, x, y=None, controller=None):
		if not actor._resources_loaded:
			actor.load_resources()

		if y is None:
			y = self.ground.height_at(x)
		actor.pos = Vec2(x, y)
		actor.level = self

		if controller is not None:
			actor.controller = controller
			self.controllers.append(controller)

		from bamboo.actors.samurai import Character
		from bamboo.actors.trees import Climbable
		if isinstance(actor, Character):
			self.characters.append(actor)
		elif isinstance(actor, Climbable):
			if actor.is_climbable():
				self.climbables.append(actor)
		self.actors.append(actor)
		actor.on_spawn()

	def kill(self, actor):
		from bamboo.actors.samurai import Character
		from bamboo.actors.trees import Climbable
		if isinstance(actor, Character):
			self.characters.remove(actor)
		elif isinstance(actor, Climbable):
			try:
				self.climbables.remove(actor)
			except ValueError:
				pass
		self.actors.remove(actor)
		if actor.controller:
			actor.controller.on_character_death()
			self.controllers.remove(actor.controller)
		actor.delete()
		actor.level = None

	def get_actors(self):
		return self.actors[:]

	def update_scenery(self):
		"""Update only scenery objects - for menus"""
		from bamboo.actors.scenery import Campfire
		from bamboo.actors.particles import Smoke
		self.ground.update()
		for a in self.actors:
			if isinstance(a, Campfire) or isinstance(a, Smoke):
				a.update() 

	def update(self):
		"""Run physics, update everything in the world"""
		from bamboo.actors.characters import Character
		self.ground.update()

		for c in self.controllers:
			c.update()

#		self.collide()

		for a in self.actors:
			if isinstance(a, Character):
				if a.pos.x < 0:
					a.pos = Vec2(0, a.pos.y)
				elif a.pos > self.width:
					# TODO: fire level completion event
					pass
			a.update()

	def collide(self):
		for i, a in enumerate(self.characters):
			for b in self.characters[i+1:]:
				intersection = a.bounds().intersection(b.bounds())
				if intersection:
					d = min(intersection.w, intersection.h) # amount of intersection
					ab = (b.pos - a.pos)
					if not ab:
						ab = Vec2(0, 1)
					v = ab.normalized() # direction AB
					a.pos -= v
					b.pos += v

	def get_climbables(self):
		for a in self.climbables:
			yield a

	def get_nearest_climbable(self, pos):
		"""Return the nearest climbable and the distance to that climbable."""
		nearest = None
		distance = None
		for a in self.get_climbables():
			d = a.distance_from(pos)
			if nearest is None or d < distance:
				nearest = a
				distance = d

		return nearest, distance

	def find_playercharacters(self):
		return [a for a in self.characters if a.is_pc]

	def characters_colliding(self, rect):
		return [a for a in self.characters if a.bounds().intersects(rect)]
		
