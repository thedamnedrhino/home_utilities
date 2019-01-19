from tabulate import tabulate
import optparse
import re


OUTPUT=['name', 'protein/dol', 'protein/unit', 'price/unit']
INPUT=['name', 'protein/unit', 'price/unit']
UNITS=['%dGR', '%dML', '%s']


class Unit:
	COEFF_SETS = [('kg', 'gr', 'oz'), ('l', 'ml', 'oz')]
	COEFFS = {
		'kg': ('gr', 1000),
		'oz': ('gr', 28.34),
		'l': ('ml', 1000),
		'oz': ('ml', 28.34)
	}
	ALIASES = {'g': 'gr', 'cc': 'ml'}

	def __init__(self, name, n):
		self.name = name.lower()
		if self.name in self.ALIASES:
			self.name = self.ALIASES[self.name]
		self.n = n if n is not None else 1

	def compatible(self, other):
		u1 = self.name
		u2 = other.name
		if u1 == u2:
			return True
		for s in self.COEFF_SETS:
			if u1 in s and u2 in s:
				return True
		return False
	
	def coefficient(self, other):
		c1 = 1 if self.name not in self.COEFFS else self.COEFFS[self.name][1]	
		c2 = 1 if other.name not in self.COEFFS else self.COEFFS[other.name][1]	
		return self.n / other.n * c1 / c2
	
	def __repr__(self):
		return "{} {}".format(self.n, self.name)

class ValuePerU:
	def __init__(self, amount: float, unit: Unit):
		self.amount = amount
		self.unit = unit
	
	def compatible(self, other):
		return self.unit.compatible(other.unit)
	
	def __repr__(self):
		return "{}/{}".format(self.amount, self.unit)


class Food:
	def __init__(self, name, protdol: float, protperu: ValuePerU, priceperu: ValuePerU):
		self.name = name
		self.protdol = protdol
		self.protu = protperu
		self.priceu = priceperu
		
	@staticmethod
	def create(name, proteinvalueperu, pricevalueperu):
		if proteinvalueperu is None \
			or pricevalueperu is None \
			or not proteinvalueperu.compatible(pricevalueperu):
			return	Food(name, None, proteinvalueperu, pricevalueperu) 
		p = proteinvalueperu
		pc = pricevalueperu
		protdol = p.amount / (pc.amount * p.unit.coefficient(pc.unit))
		return Food(name, protdol, p, pc)

def parse_unit_amount(s, quantity_name: str):
	parts = s.split('/')
	assert len(parts) == 2, "The {}/unit provided is not of the right format: {}. The correct format is e.g: 100/1-kg".format(quantity_name, s)
	amount = float(parts[0])
	u = parts[1]
	parts = u.split('-')
	assert len(parts) == 2, "The {}/unit provided is not of the right format: {}. The correct format is e.g: 100/1-kg".format(quantity_name, s)	
	unit = Unit(parts[1], float(parts[0]))
	vpu = ValuePerU(amount, unit)
	return vpu

def getfood(inp):
	protein = parse_unit_amount(inp[1], 'protein') if '/' in inp[1] else None
	price = parse_unit_amount(inp[2], 'price') if len(inp) > 2 and '/' in inp[2] else None
	food = Food.create(inp[0], protein, price)
	return food	


def getrow(food):
	return [food.name, food.protdol, food.protu, food.priceu]	


def printfoods(foods):
	header = ['Name', 'Protein/$', 'Protein/Unit', 'Price/Unit']
	rows = [getrow(food) for food in foods]
	print(tabulate(rows, header))


if __name__ == '__main__':
	optparser = optparse.OptionParser()
	optparser.add_option("-i", "--inputfile", dest="inputfile", default=None, help="filename in the conll format")
	(opts, _) = optparser.parse_args()
	if opts.inputfile is None:
		raise Exception('no input file')
	with open(opts.inputfile) as f:
		rows = [[e.strip() for e in l.split(',')] for l in f.readlines() if l]

	print(rows)
	has_header = bool(re.match(r"[a-zA-Z]", rows[0][1]))
	print("{}".format('true' if has_header else 'false'))
	food_rows = rows[1 if has_header else 0:]
	foods = [getfood(r) for r in food_rows if r and len(r[0]) > 0]
	printfoods(foods)
