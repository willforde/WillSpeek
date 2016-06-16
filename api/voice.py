class Voice(object):
	""" Voice data object """
	def __init__(self, token, id, name, gender=None, languages=None):
		self.__id = id
		self.__name = name
		self.__gender = gender
		self.__languages = languages
		self._token = token
	
	@property
	def id(self):
		""" Return the id of the voice """
		return self.__id
	
	@property
	def id_basic(self):
		return self.__id.rsplit("\\",1)[-1]
	
	@property
	def name(self):
		""" Return the name of the voice """
		return self.__name
	
	@property
	def gender(self):
		""" Return the gender of the voice """
		return self.__gender
	
	@property
	def languages(self):
		""" Return the languages of the voice """
		return self.__languages
	
	def __str__(self):
		return """<Voice id=%s name=%s languages=%s gender=%s>""" % (self.__id, self.__name, self.__languages, self.__gender)