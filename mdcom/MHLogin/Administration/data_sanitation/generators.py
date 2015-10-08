
import random

from data.streets import STREET_FIRST, \
				STREET_SECOND, STREET_THIRD, UNIT_TYPES, UNIT_ALPHA
from data.names import MALE_FIRST_NAMES,\
				FEMALE_FIRST_NAMES, SURNAMES

from lorem import do_lorem


def genMaleFirstName():
	return MALE_FIRST_NAMES[random.randrange(len(MALE_FIRST_NAMES))]


def genFemaleFirstName():
	return FEMALE_FIRST_NAMES[random.randrange(len(FEMALE_FIRST_NAMES))]


def genSurname():
	return SURNAMES[random.randrange(len(SURNAMES))]


def genUsername(firstName, lastName, id):
	return '%s%s%i' % (
					firstName[0],
					lastName,
					id,
				)


def genEmail(username=None):
	if (not username):
		username = genUsername(genMaleFirstName(), genSurname(), random.randint(1, 999))
	return '%s@%s' % (
					username,
					'myhealthincorporated.com',
				)


def genAddress1():
	return '%i %s %s %s' % (
					random.randrange(10000),
					STREET_FIRST[random.randrange(len(STREET_FIRST))],
					STREET_SECOND[random.randrange(len(STREET_SECOND))],
					STREET_THIRD[random.randrange(len(STREET_THIRD))],
				)


def genAddress2():
	prefixAlpha = random.randrange(10)
	if (prefixAlpha < 4):
		return '%s %s%i' % (
						UNIT_TYPES[random.randrange(len(UNIT_TYPES))],
						UNIT_ALPHA[random.randrange(len(UNIT_ALPHA))],
						random.randrange(1000),
					)

	postfixAlpha = random.randrange(10)
	if (postfixAlpha < 4):
		return '%s %i%s' % (
						UNIT_TYPES[random.randrange(len(UNIT_TYPES))],
						random.randrange(1000),
						UNIT_ALPHA[random.randrange(len(UNIT_ALPHA))],
					)

	return '%s %i' % (
					UNIT_TYPES[random.randrange(len(UNIT_TYPES))],
					random.randrange(1000),
				)


def genPhone():
	# Return 800-goog-411 for now.
	return '8004664411'
	return ''.join([str(random.randrange(10)) for i in range(10)])


def genMessage(length):
	if (length == 0):
		return ''
	if (length == 1):
		return '.'

	#raise Exception(dir(lipsum))
	newMessage = do_lorem(0, 0, length, 0, 0)

	if (newMessage[length - 2] == ' ' or newMessage[length - 2] == '\n'):
		# white space before the period.
		return ''.join([newMessage[:(length - 2)], 'a.'])
	else:
		return ''.join([newMessage[:(length - 1)], '.'])

	return newMessage

