import z3

def basis_is_normalized():
  basis1_x = z3.Int("basis1_x")
  basis1_y = z3.Int("basis1_y")
  basis2_x = z3.Int("basis2_x")
  basis2_y = z3.Int("basis2_y")

  # Basis elements in the two specified quadrants (strictly)
  yield basis1_x <= 0
  yield basis1_y > 0
  yield basis2_x > 0
  yield basis2_y >= 0

  # All of the comparisons neccesary to verify L-infinity minimality; the rest are obvious.
  yield basis1_y + basis2_y >= basis2_x
  yield basis1_y + basis2_y >= -basis1_x
  yield basis2_x - basis1_x >= basis1_y
  yield basis2_x - basis1_x >= basis2_y

  # TODO:  normalizations that rotate/mirror the lattice.  positive dot
  # product?  first one longer than second?

  yield basis1_x*basis2_x + basis1_y*basis2_y >= 0
  yield basis1_x*basis1_x + basis1_y*basis1_y >= basis2_x*basis2_x + basis2_y*basis2_y

  # TODO:  because the L-infinity norm is kinda dumb, there are duplicates here.

def point_inbounds(x, y):
  # This same logic is implemented in pretty_print.
  basis1_x = z3.Int("basis1_x")
  basis1_y = z3.Int("basis1_y")
  basis2_x = z3.Int("basis2_x")
  basis2_y = z3.Int("basis2_y")

  yield x >= basis1_x
  yield x < basis2_x
  yield y >= 0
  pivot = basis1_x + basis2_x
  yield z3.Or(z3.And(y < basis1_y, x < pivot), z3.And(y < basis2_y, x >= pivot))

def build_model(num_crushers, num_washers, num_chems):
  basis1_x = z3.Int("basis1_x")
  basis1_y = z3.Int("basis1_y")
  basis2_x = z3.Int("basis2_x")
  basis2_y = z3.Int("basis2_y")

  washer_x = z3.Ints(" ".join(f"washer-x-{ix}" for ix in range(num_washers)))
  washer_y = z3.Ints(" ".join(f"washer-y-{ix}" for ix in range(num_washers)))
  crusher_x = z3.Ints(" ".join(f"crusher-x-{ix}" for ix in range(num_crushers)))
  crusher_y = z3.Ints(" ".join(f"crusher-y-{ix}" for ix in range(num_crushers)))
  chem_x = z3.Ints(" ".join(f"chem-x-{ix}" for ix in range(num_chems)))
  chem_y = z3.Ints(" ".join(f"chem-y-{ix}" for ix in range(num_chems)))

  s = z3.Solver()

  s.add(z3.And(*basis_is_normalized()))

  # Minimum basis size to accomodate a washer.
  s.add(z3.Or(basis1_x <= -5, basis1_y >= 5))
  s.add(z3.Or(basis2_x >= 5, basis2_y >= 5))

  for x, y in zip(washer_x + crusher_x + chem_x, washer_y + crusher_y + chem_y):
    s.add(z3.And(*point_inbounds(x, y)))

  # break symmetry
  s.add(washer_x[0] == 0)
  s.add(washer_y[0] == 0)

  for i in range(num_crushers):
    for j in range(i+1, num_crushers):
      s.add(z3.Or(crusher_x[i] < crusher_x[j], z3.And(crusher_x[i] == crusher_x[j], crusher_y[i] < crusher_y[j])))
  for i in range(num_washers):
    for j in range(i+1, num_washers):
      s.add(z3.Or(washer_x[i] < washer_x[j], z3.And(washer_x[i] == washer_x[j], washer_y[i] < washer_y[j])))
  for i in range(num_chems):
    for j in range(i+1, num_chems):
      s.add(z3.Or(chem_x[i] < chem_x[j], z3.And(chem_x[i] == chem_x[j], chem_y[i] < chem_y[j])))

  def get_basic_offsets():
    for b1 in range(-5, 6):
      for b2 in range(-5, 6):
        yield (basis1_x*b1 + basis2_x*b2, basis1_y*b1+basis2_y*b2)

  def non_overlap2(c1, c2, size, dim):
    return z3.And(
        z3.Or(c1-c2 >= size, c1-c2 <= -size),
        z3.Or(c1-c2+dim >= size, c1-c2+dim <= -size),
        z3.Or(c1-c2-dim >= size, c1-c2-dim <= -size))

  def non_overlap(x1, x2, y1, y2, size):
    reqs = []
    for (xoff, yoff) in get_basic_offsets():
      reqs.append(z3.Or(
          x1-x2+xoff >= size,
          x1-x2+xoff <= -size,
          y1-y2+yoff >= size,
          y1-y2+yoff <= -size))
    return z3.And(reqs)

  for a in range(num_washers):
    for b in range(a+1, num_washers):
      s.add(non_overlap(washer_x[a], washer_x[b], washer_y[a], washer_y[b], 5))
  for a in range(num_chems):
    for b in range(a+1, num_chems):
      s.add(non_overlap(chem_x[a], chem_x[b], chem_y[a], chem_y[b], 3))
  for a in range(num_crushers):
    for b in range(a+1, num_crushers):
      s.add(non_overlap(crusher_x[a], crusher_x[b], crusher_y[a], crusher_y[b], 3))
  for w in range(num_washers):
    for c in range(num_crushers):
      s.add(non_overlap(washer_x[w], crusher_x[c], washer_y[w], crusher_y[c], 4))
  for w in range(num_washers):
    for h in range(num_chems):
      s.add(non_overlap(washer_x[w], chem_x[h], washer_y[w], chem_y[h], 4)) # FIXME
  for c in range(num_crushers):
    for h in range(num_chems):
      s.add(non_overlap(crusher_x[c], chem_x[h], crusher_y[c], chem_y[h], 3))


  def get_links(x1, x2, y1, y2, size):
    LENGTH = 4
    links = []
    for (xoff, yoff) in get_basic_offsets():
      links.append(z3.And(
        x1-x2+xoff > -size,
        x1-x2+xoff < size,
        y1-y2+yoff > -size-LENGTH,
        y1-y2+yoff < size+LENGTH,
        z3.Or(y1-y2+yoff > size, y1-y2+yoff < -size)))
      links.append(z3.And(
        y1-y2+yoff > -size,
        y1-y2+yoff < size,
        x1-x2+xoff > -size-LENGTH,
        x1-x2+xoff < size+LENGTH,
        z3.Or(x1-x2+xoff > size, x1-x2+xoff < -size)))
    return links
  for w in range(num_washers):
    links = []
    for c in range(num_crushers):
      links += get_links(washer_x[w], crusher_x[c], washer_y[w], crusher_y[c], 4)
    s.add(z3.PbGe([(l, 1) for l in links], 6))
  for c in range(num_crushers):
    links = []
    for h in range(num_chems):
      links += get_links(crusher_x[c], chem_x[h], crusher_y[c], chem_y[h], 3)
    s.add(z3.PbGe([(l, 1) for l in links], 2))

  return s

def pretty_print(model, num_crushers, num_washers, num_chems):
  basis1_x = model[z3.Int("basis1_x")].as_long()
  basis1_y = model[z3.Int("basis1_y")].as_long()
  basis2_x = model[z3.Int("basis2_x")].as_long()
  basis2_y = model[z3.Int("basis2_y")].as_long()
  if basis2_y != 0 or basis1_x != 0:
    return
  result = [[" " for _ in range(basis2_x)] for _ in range(basis1_y)]
  for w in range(num_washers):
    y = model[z3.Int(f"washer-y-{w}")].as_long()
    x = model[z3.Int(f"washer-x-{w}")].as_long()
    for yy in [y, (y-1)%basis1_y, (y-2)%basis1_y, (y+1)%basis1_y, (y+2)%basis1_y]:
      for xx in [x, (x-1)%basis2_x, (x-2)%basis2_x, (x+1)%basis2_x, (x+2)%basis2_x]:
        result[yy][xx] = "W"
  for c in range(num_crushers):
    y = model[z3.Int(f"crusher-y-{c}")].as_long()
    x = model[z3.Int(f"crusher-x-{c}")].as_long()
    for yy in [y, (y-1)%basis1_y, (y+1)%basis1_y]:
      for xx in [x, (x-1)%basis2_x, (x+1)%basis2_x]:
        result[yy][xx] = "c"
  for h in range(num_chems):
    y = model[z3.Int(f"chem-y-{h}")].as_long()
    x = model[z3.Int(f"chem-x-{h}")].as_long()
    for yy in [y, (y-1)%basis1_y, (y+1)%basis1_y]:
      for xx in [x, (x-1)%basis2_x, (x+1)%basis2_x]:
        result[yy][xx] = "h"
  header = "+" + "-"*basis2_x + "+"
  return header + "\n" + "\n".join("|" + "".join(row) + "|" for row in result) + "\n" + header

def pretty_print2(model, num_crushers, num_washers, num_chems):
  basis1_x = model[z3.Int("basis1_x")].as_long()
  basis1_y = model[z3.Int("basis1_y")].as_long()
  basis2_x = model[z3.Int("basis2_x")].as_long()
  basis2_y = model[z3.Int("basis2_y")].as_long()

  bound_x = basis2_x - basis1_x
  bound_y = max(basis1_y, basis2_y)
  pivot_x = basis2_x

  result = (
      [["+"] + ["-"]*bound_x + ["+"]] +
      [["|"] + [" "]*bound_x + ["|"] for x in range(bound_y)] +
      [["+"] + ["-"]*bound_x + ["+"]]
  )

  result[bound_y+1][bound_x+1] = " "
  result[basis2_y+1][bound_x+1] = "+"
  result[bound_y+1][pivot_x+1] = "+"
  result[basis2_y+1][pivot_x+1] = "+"
  for x in range(pivot_x+2, bound_x+1):
    result[bound_y+1][x] = " "
    result[basis2_y+1][x] = "-"
  for y in range(basis2_y+2, bound_y+1):
    result[y][bound_x+1] = " "
    result[y][pivot_x+1] = "|"

  result[bound_y+1][0] = " "
  result[basis1_y+1][0] = "+"
  result[bound_y+1][pivot_x] = "+"
  result[basis1_y+1][pivot_x] = "+"
  for x in range(1, pivot_x):
    result[bound_y+1][x] = " "
    result[basis1_y+1][x] = "-"
  for y in range(basis1_y+2, bound_y+1):
    result[y][0] = " "
    result[y][pivot_x] = "|"

  def get_lattice_offsets():
    for b1 in range(-40, 50):
      for b2 in range(-40, 50):
        yield (basis1_x*b1 + basis2_x*b2, basis1_y*b1+basis2_y*b2)
  def get_building_offsets(size):
    for x in range(-size, size+1):
      for y in range(-size, size+1):
        yield (x, y)
  def write_sym(x, y, sym):
    if x < 0 or x >= bound_x or y < 0:
      return
    if x < pivot_x and y < basis1_y:
      result[y+1][x+1] = sym
    if x >= pivot_x and y < basis2_y:
      result[y+1][x+1] = sym

  for w in range(num_washers):
    xbase = model[z3.Int(f"washer-x-{w}")].as_long()
    ybase = model[z3.Int(f"washer-y-{w}")].as_long()
    for (xlat, ylat) in get_lattice_offsets():
      for (xoff, yoff) in get_building_offsets(2):
        write_sym(xbase+xlat+xoff, ybase+ylat+yoff, "W")
  for c in range(num_crushers):
    xbase = model[z3.Int(f"crusher-x-{c}")].as_long()
    ybase = model[z3.Int(f"crusher-y-{c}")].as_long()
    for (xlat, ylat) in get_lattice_offsets():
      for (xoff, yoff) in get_building_offsets(1):
        write_sym(xbase+xlat+xoff, ybase+ylat+yoff, "c")
  for h in range(num_chems):
    xbase = model[z3.Int(f"chem-x-{h}")].as_long()
    ybase = model[z3.Int(f"chem-y-{h}")].as_long()
    for (xlat, ylat) in get_lattice_offsets():
      for (xoff, yoff) in get_building_offsets(1):
        write_sym(xbase+xlat+xoff, ybase+ylat+yoff, "h")

  return "\n".join("".join(row) for row in result)

def fundamental_area():
  return - z3.Int("basis1_x")*z3.Int("basis2_y") + z3.Int("basis1_y")*z3.Int("basis2_x")

def is_rectilinear():
  return z3.And(z3.Int("basis1_x") == 0, z3.Int("basis2_y") == 0)

def get_all_solutions(s):
  while repr(s.check()) == "sat":
    yield s.model()
    constraints = []
    for var in s.model():
      var = z3.Int(repr(var))
      constraints.append(var != s.model()[var].as_long())
    s.add(z3.Or(constraints))

def do_diagonal(min_area=50, max_area=100, num_crushers=4, num_washers=2, num_chems=2):
  slv = build_model(num_crushers, num_washers, num_chems)
  slv.add(fundamental_area() >= min_area)
  slv.add(fundamental_area() <= max_area)
  for model in get_all_solutions(slv):
    print(slv.model().evaluate(fundamental_area()))
    print(pretty_print2(model, num_crushers, num_washers, num_chems))
