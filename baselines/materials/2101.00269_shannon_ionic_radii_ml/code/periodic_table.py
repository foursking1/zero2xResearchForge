"""Periodic-table reference tables for feature engineering.

These are static reference constants (element symbol -> atomic number,
period, group, block, valence-electron configuration descriptor, first
ionization potential). They are NOT part of the frozen data package but are
standard chemical reference values used to build model features, mirroring
the paper's stated feature set (period number, valence electronic
configuration, oxidation state, coordination number, ionization potential).
"""

# element symbol -> (atomic_number, period, group, block, first_ionization_potential_eV)
# group follows IUPAC 1-18; lanthanides/actinides assigned group 3 + block 'f'.
# IP values are standard experimental first ionization potentials (eV).
PERIODIC_TABLE = {
    "H": (1, 1, 1, "s", 13.598),   "He": (2, 1, 18, "s", 24.587),
    "Li": (3, 2, 1, "s", 5.392),   "Be": (4, 2, 2, "s", 9.323),
    "B": (5, 2, 13, "p", 8.298),   "C": (6, 2, 14, "p", 11.260),
    "N": (7, 2, 15, "p", 14.534),  "O": (8, 2, 16, "p", 13.618),
    "F": (9, 2, 17, "p", 17.423),  "Ne": (10, 2, 18, "p", 21.565),
    "Na": (11, 3, 1, "s", 5.139),  "Mg": (12, 3, 2, "s", 7.646),
    "Al": (13, 3, 13, "p", 5.986), "Si": (14, 3, 14, "p", 8.152),
    "P": (15, 3, 15, "p", 10.487), "S": (16, 3, 16, "p", 10.360),
    "Cl": (17, 3, 17, "p", 12.968), "Ar": (18, 3, 18, "p", 15.760),
    "K": (19, 4, 1, "s", 4.341),   "Ca": (20, 4, 2, "s", 6.113),
    "Sc": (21, 4, 3, "d", 6.562),  "Ti": (22, 4, 4, "d", 6.828),
    "V": (23, 4, 5, "d", 6.746),   "Cr": (24, 4, 6, "d", 6.767),
    "Mn": (25, 4, 7, "d", 7.434),  "Fe": (26, 4, 8, "d", 7.902),
    "Co": (27, 4, 9, "d", 7.881),  "Ni": (28, 4, 10, "d", 7.640),
    "Cu": (29, 4, 11, "d", 7.726), "Zn": (30, 4, 12, "d", 9.394),
    "Ga": (31, 4, 13, "p", 5.999), "Ge": (32, 4, 14, "p", 7.899),
    "As": (33, 4, 15, "p", 9.789), "Se": (34, 4, 16, "p", 9.752),
    "Br": (35, 4, 17, "p", 11.814), "Kr": (36, 4, 18, "p", 13.999),
    "Rb": (37, 5, 1, "s", 4.177),  "Sr": (38, 5, 2, "s", 5.695),
    "Y": (39, 5, 3, "d", 6.217),   "Zr": (40, 5, 4, "d", 6.634),
    "Nb": (41, 5, 5, "d", 6.759),  "Mo": (42, 5, 6, "d", 7.092),
    "Tc": (43, 5, 7, "d", 7.28),   "Ru": (44, 5, 8, "d", 7.360),
    "Rh": (45, 5, 9, "d", 7.459),  "Pd": (46, 5, 10, "d", 8.337),
    "Ag": (47, 5, 11, "d", 7.576), "Cd": (48, 5, 12, "d", 8.994),
    "In": (49, 5, 13, "p", 5.786), "Sn": (50, 5, 14, "p", 7.344),
    "Sb": (51, 5, 15, "p", 8.608), "Te": (52, 5, 16, "p", 9.010),
    "I": (53, 5, 17, "p", 10.451), "Xe": (54, 5, 18, "p", 12.130),
    "Cs": (55, 6, 1, "s", 3.894),  "Ba": (56, 6, 2, "s", 5.212),
    "La": (57, 6, 3, "f", 5.577),  "Ce": (58, 6, 3, "f", 5.539),
    "Pr": (59, 6, 3, "f", 5.473),  "Nd": (60, 6, 3, "f", 5.525),
    "Pm": (61, 6, 3, "f", 5.582),  "Sm": (62, 6, 3, "f", 5.644),
    "Eu": (63, 6, 3, "f", 5.670),  "Gd": (64, 6, 3, "f", 6.150),
    "Tb": (65, 6, 3, "f", 5.864),  "Dy": (66, 6, 3, "f", 5.939),
    "Ho": (67, 6, 3, "f", 6.022),  "Er": (68, 6, 3, "f", 6.108),
    "Tm": (69, 6, 3, "f", 6.184),  "Yb": (70, 6, 3, "f", 6.254),
    "Lu": (71, 6, 3, "f", 5.426),  "Hf": (72, 6, 4, "d", 6.825),
    "Ta": (73, 6, 5, "d", 7.550),  "W": (74, 6, 6, "d", 7.864),
    "Re": (75, 6, 7, "d", 7.834),  "Os": (76, 6, 8, "d", 8.438),
    "Ir": (77, 6, 9, "d", 8.967),  "Pt": (78, 6, 10, "d", 8.959),
    "Au": (79, 6, 11, "d", 9.226), "Hg": (80, 6, 12, "d", 10.437),
    "Tl": (81, 6, 13, "p", 6.108), "Pb": (82, 6, 14, "p", 7.417),
    "Bi": (83, 6, 15, "p", 7.286), "Po": (84, 6, 16, "p", 8.414),
    "At": (85, 6, 17, "p", 9.318), "Rn": (86, 6, 18, "p", 10.748),
    "Fr": (87, 7, 1, "s", 4.073),  "Ra": (88, 7, 2, "s", 5.279),
    "Ac": (89, 7, 3, "f", 5.170),  "Th": (90, 7, 3, "f", 6.307),
    "Pa": (91, 7, 3, "f", 5.890),  "U": (92, 7, 3, "f", 6.194),
    "Np": (93, 7, 3, "f", 6.266),  "Pu": (94, 7, 3, "f", 6.026),
    "Am": (95, 7, 3, "f", 5.993),  "Cm": (96, 7, 3, "f", 5.990),
    "Bk": (97, 7, 3, "f", 6.198),  "Cf": (98, 7, 3, "f", 6.282),
    "Es": (99, 7, 3, "f", 6.420),  "Fm": (100, 7, 3, "f", 6.500),
    "Md": (101, 7, 3, "f", 6.580), "No": (102, 7, 3, "f", 6.650),
}

# number of valence electrons by group (IUPAC) for main-group; for d/f blocks
# we use the d/f shell occupation proxy described in the report.
def valence_electrons(symbol):
    z, period, group, block, ip = PERIODIC_TABLE[symbol]
    if block == "s":
        return group
    if block == "p":
        return group - 10
    if block == "f":
        return 3
    # d-block rough count of d electrons beyond [n-1]d1 s2 for group>=3
    return max(1, group - 2)