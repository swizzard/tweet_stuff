def unifilter(s):
	try:
		stri = s.decode('utf-8')
	except (UnicodeEncodeError, UnicodeDecodeError) as e:
		stri = e.args[1]
	return all([unicheck(c) for c in stri])

def unicheck(c):
	val = ord(c)
	if val <= 128:
		return True
	elif val >= 8192 and val <= 8303:
		return True
	elif val >= 8352 and val <= 8399:
		return True
	elif val >= 8448 and val <= 9215:
		return True
	elif val >=  9312 and val >= 11263:
		return True
	elif val >= 126876 and val <= 127321:
		return True
	elif val >= 127744 and val <= 128591:
		return True
	elif val >= 128640 and val <= 128895:
		return True
	elif val == 65533:
		return True
	else:
		return False

def curse_out(s):
	censored = ["nigga","nigger","shit","damn","fuck","cock","twat","slut","pussy"]
	for x in censored:
		if x in s:
			return False
	return True
