import numpy as np

from xkcd_colors import xkcd_colors


class Event:
    pass


class Particle(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value


class ParticleArray:
    def __init__(self, branches={}):
        self.keys = list(branches.keys())
        self.__dict__.update(branches)

    def dict(self):
        return {k: getattr(self, k) for k in self.keys}

    def __len__(self):
        if not self.keys: return 0
        return len(getattr(self, self.keys[0]))

    def __getitem__(self, where):
        return ParticleArray({k: getattr(self, k)[where] for k in self.keys})

    def list(self):
        d = self.dict()
        return [Particle(**{k: v[i] for k, v in d.items()}) for i in range(len(self))]

    def subtree(self, node_index, depth=0, parent=None, available=None):
        if available is None: available = {}
        if node_index is None: raise Exception('node_index is None gives hard-to-decipher errors')
        if node_index in available:
            particle = available[node_index]
            if parent:
                particle.parents.append(parent)
                parent.children.append(particle)
            return
        else:
            particle = Particle(**{k: v[node_index] for k, v in self.dict().items()})
            available[node_index] = particle
            particle.index = node_index
            particle.depth = depth
            particle.parents = []
            particle.children = []
            if parent:
                particle.parents.append(parent)
                parent.children.append(particle)
            particle.is_leaf = particle.d1==-1
            yield particle
            if particle.is_leaf: return
            for child_index in range(particle.d1, particle.d2+1):
                yield from self.subtree(child_index, depth+1, parent=particle, available=available)

    def root_indices(self):
        has_parent = np.zeros(len(self), dtype=bool)
        for i in range(len(self)):
            if self.d1[i]==-1: continue
            has_parent[self.d1[i]:self.d2[i]+1] = True
        return np.nonzero(~has_parent)[0]

    def roots(self):
        return [list(self.subtree(i) for i in self.root_indices())]

    def lowest_status_zprime_index(self):
        return np.argmin(self.status[self.pid==4900023])

    def lowest_status_zprime_descendants(self):
        return list(self.subtree(self.lowest_status_zprime_index()))

    def highest_status_zprime_index(self):
        return np.argmax(np.where(self.pid==4900023, self.status, -1))

    def highest_status_zprime_descendants(self):
        particles = list(self.subtree(self.highest_status_zprime_index()))
        if not particles: print('Warning: Empty list of particles!')
        return particles


def get_event(tree, i=0):
    event = Event()
    event.index = i

    # Build particles array
    branches = [
        'PID', 'E', 'Eta', 'PT',
        'Phi', 'Px', 'Py', 'Pz',
        'Rapidity', 'Status', 'Mass',
        'D1', 'D2',
        'T', 'X', 'Y', 'Z'
        ]
    arrays = {
        b.lower(): tree['Particle.'+b].array(entry_start=i, entry_stop=i+1)[0]
        for b in branches
        }
    event.particles = ParticleArray(arrays)

    # Build list of jets
    event.jets = ParticleArray({
        b.lower(): tree['GenJet08.'+b].array(entry_start=i, entry_stop=i+1)[0]
        for b in ['PT', 'Eta', 'Phi']
        }).list()        
    constituent_indices = tree['GenJet08.Constituents'].array(entry_start=i, entry_stop=i+1)['refs']
    for i in range(len(event.jets)):
        event.jets[i].constituent_indices = constituent_indices[i].to_numpy()

    return event



class ColorWheel:
    '''Returns a consistent color when given the same object'''
    def __init__(self, assignments=None, colors=None, seed=1001, shuffle=True):
        self.colors = list(xkcd_colors.values()) if colors is None else colors
        if shuffle:
            np.random.seed(seed)
            np.random.shuffle(self.colors)
        self._original_colors = self.colors.copy()
        self.assigned_colors = {}
        if assignments: [self.assign(k, v) for k, v in assignments.items()]
        
    def __contains__(self, key):
        return key in self.assigned_colors

    def __call__(self, key):
        if key in self.assigned_colors:
            return self.assigned_colors[key]
        else:
            color = self.colors.pop()
            self.assigned_colors[key] = color
            if not(self.colors): self.colors = self._original_colors.copy()
            return color
    
    def assign(self, key, color):
        """Assigns a specific color to a thing"""
        self.assigned_colors[key] = color
        if color in self.colors: self.colors.remove(color)

    def many(self, things, color=None):
        for i, t in enumerate(things):
            if color is None and i == 0:
                color = self(t)
            else:
                self.assign(t, color)


class PropertyWheel:

    def __init__(self):
        self.colorwheel = ColorWheel()
        self.titles = {}
        self.assign(4900023, 'red', 'Zprime')
        self.assign(4900101, 'orange', 'Dark quarks')
        self.assign(4900021, 'tomato', 'Dark gluons')
        self.assign(22, xkcd_colors['apple green'], 'Photons')
        self.many([4900111, 4900211, 4900113, 4900213], 'tomato', 'Dark particles')
        self.many(list(range(100, 1000)), 'skyblue', 'SM particles')
        self.many(list(range(1, 7)), 'green', 'SM quarks')
        self.many(list(range(11, 17)), 'blue', 'SM leptons')


    def assign(self, key, color, title):
        self.colorwheel.assign(key, color)
        self.titles[key] = title


    def many(self, keys, color, title):
        self.colorwheel.many(keys, color)
        for key in keys: self.titles[key] = title


    def __call__(self, key):
        return self.colorwheel(key), self.titles.get(key, '?')
