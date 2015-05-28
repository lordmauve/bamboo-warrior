from bamboo.geom import Rect, Vec2
from bamboo.scene import Viewport


class Camera(object):
	"""A camera generates a viewport - ie. a place in the scene"""
	def __init__(self, width, height):
		self.width = width
		self.height = height

	def get_viewport(self):
		raise NotImplementedError("Subclasses must implement camera.get_viewport()") 

	@classmethod
	def for_window(cls, window, *args, **kwargs):
		ka = {}
		ka.update(kwargs)
		ka['width'] = window.width
		ka['height'] = window.height
		return cls(*args, **ka)


class FixedCamera(Camera):
	"""A camera with a fixed position"""
	scale = 1
	def __init__(self, width, height, center=Vec2(0, 0)):
		super(FixedCamera, self).__init__(width, height)
		self.center = center

	def move_to(self, pos):
		# NB: floating point camera centers can cause fringes on sprites
		# integer camera centers seem jumpy
		self.center = Vec2(x, y)

	def get_viewport(self):
		return Viewport(self.width, self.height, center_x=self.center.x, center_y=self.center.y, scale=self.scale)


class MovingCamera(FixedCamera):
	"""A camera that controls its own position""" 
	def update(self):
		"""Implement this to reposition the camera, etc."""

	def track(self, pos):
		"""Implement this to set where the camera should be looking"""
		self.move_to(pos)

	def get_viewport(self):
		self.update()
		return super(MovingCamera, self).get_viewport()


class TrackingCamera(MovingCamera):
	"""A camera that follows an actor"""
	def __init__(self, actor, width, height):
		super(TrackingCamera, self).__init__(width, height)
		self.actor = actor

	def update(self):
		if self.actor.is_alive():
			self.move_to(self.actor.pos)


class LevelCamera(MovingCamera):
	"""A camera that is restricted to the visible region of a level"""
	def __init__(self, width, height, level, center=Vec2(0, 0)):
		super(LevelCamera, self).__init__(width, height, center)
		self.level = level

	def move_to(self, pos):
		hw = self.width * self.scale / 2.0
		hh = self.height * self.scale / 2.0
		x = max(hw, min(self.level.width - hw, pos.x))
		y = max(hh, pos.y)
		# NB: floating point camera centers can cause fringes on sprites
		# integer camera centers seem jumpy
		self.center = Vec2(x, y)


class RegionTrackingCamera(LevelCamera):
	"""A camera that tracks a subject ony when the subject moves out of a frame that is centered on the current viewport"""
	def __init__(self, width, height, level, center=Vec2(0,0), xfrac=0.5, yfrac=None):
		super(RegionTrackingCamera, self).__init__(width, height, level, center)
		self.xfrac = xfrac
		self.yfrac = yfrac or xfrac
		self.dest = None

	def get_region(self):
		return FixedCamera.get_viewport(self).bounds().scale_about_center(self.xfrac, self.yfrac)

	def update(self):
		"""Pan halfway towards dest"""
		if self.dest is not None:
			self.move_to(self.center + (self.dest - self.center) * 0.5)

	def from_region(self, p):
		"""The shortest vector to p from the focus region"""
		r = self.get_region()
		if p.x < r.l:
			x = p.x - r.l
		elif p.x > r.r:
			x = p.x - r.r
		else:
			x = 0

		if p.y < r.b:
			y = p.y - r.b
		elif p.y > r.t:
			y = p.y - r.t
		else:
			y = 0
		return Vec2(x, y)

	def track(self, p):
		"""Ensure point p is visible in the focus region"""
		self.dest = self.center + self.from_region(p)


class LeadingCamera(RegionTrackingCamera):
	"""A region tracking camera, which doesn't let the tracked object go out of frame, but tries to
	scroll the camera away in the direction of its movement"""
	last_track_point = None
	lead = Vec2(0, 0)

	def track(self, p):
		if self.last_track_point is not None:
			v = p - self.last_track_point
			if v.mag() > 100:
				self.lead *= 0.9
			else:
				self.lead = (self.lead + 0.5 * v) * 0.95
			self.center = p + self.lead 
		self.last_track_point = p
		super(LeadingCamera, self).track(p)


class DualTrackingCamera(RegionTrackingCamera):
	def track_both(self, p1, p2):
		# track the center point
		self.track(p1 + (p2 - p1) * 0.5)

		r = self.get_region()
		v = (p2 - p1)
		sep_w = abs(v.x)
		sep_h = abs(v.y)
		scale_x = sep_w / r.w
		scale_y = sep_h / r.h
		self.dest_scale = max(1, scale_x, scale_y)

	def update(self):
		super(DualTrackingCamera, self).update()
		rate = 1.001
		if self.dest_scale > self.scale:
			# if we need to zoom out, do so
			self.scale = max(1.0, min(self.dest_scale, self.scale * rate))
		else:
			# else slowly zoom back to normal
			self.scale = max(1.0, self.dest_scale, self.scale - 0.0005)
		self.scale = max(1, min(self.scale, float(self.level.width)/float(self.width)))
