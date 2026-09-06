"""Column-vector affine math; adapted from project-owned research utilities.

Matrices are nested rows. Scale/shear is nine column-major numbers.
Quaternion storage is xyzw. No engine-specific transform multiplication.
"""
import math

I4 = [[float(i == j) for j in range(4)] for i in range(4)]
I9 = [1., 0., 0., 0., 1., 0., 0., 0., 1.]
OFF_DIAGONAL = (1, 2, 3, 5, 6, 7)


def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def inverse(m):
    a = [list(row) + list(I4[i]) for i, row in enumerate(m)]
    for i in range(4):
        pivot = max(range(i, 4), key=lambda k: abs(a[k][i]))
        a[i], a[pivot] = a[pivot], a[i]
        if abs(a[i][i]) < 1e-12:
            raise ValueError("Singular affine matrix")
        divisor = a[i][i]
        a[i] = [v / divisor for v in a[i]]
        for j in range(4):
            if i != j:
                factor = a[j][i]
                a[j] = [v - factor * w for v, w in zip(a[j], a[i])]
    return [row[4:] for row in a]


def point(m, p):
    return [sum(m[i][j] * p[j] for j in range(3)) + m[i][3] for i in range(3)]


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def matrix_error(a, b):
    return max(abs(x-y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def normalized(q):
    length = math.sqrt(sum(x*x for x in q))
    if not math.isfinite(length) or length < 1e-12:
        raise ValueError("Invalid quaternion")
    return [x / length for x in q]


def rotation_matrix(q):
    x, y, z, w = normalized(q)
    return [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w), 0.],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w), 0.],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y), 0.],
            [0., 0., 0., 1.]]


def transform(t):
    r, s = rotation_matrix(t['rotation']), t['scale_shear']
    return [[sum(r[i][k]*s[j*3+k] for k in range(3)) for j in range(3)] + [t['translation'][i]] for i in range(3)] + [[0., 0., 0., 1.]]


def project_trs(t):
    return {**t, 'scale_shear': [v if i in (0, 4, 8) else 0. for i, v in enumerate(t['scale_shear'])]}


def world_matrices(bones, locals_):
    out, visiting = {}, set()
    def get(index):
        if index in out:
            return out[index]
        if index in visiting:
            raise ValueError("Skeleton cycle")
        visiting.add(index)
        parent = bones[index]['parent']
        if parent < -1 or parent >= len(bones):
            raise ValueError("Invalid parent index")
        local = transform(locals_[index])
        out[index] = multiply(get(parent), local) if parent >= 0 else local
        visiting.remove(index)
        return out[index]
    return [get(i) for i in range(len(bones))]


def skin(mesh, bones, worlds):
    palette = [multiply(w, b['inverse_bind']) for b, w in zip(bones, worlds)]
    result = []
    for p, influences in zip(mesh['positions'], mesh['skin']):
        v = [0., 0., 0.]
        for influence in influences:
            q = point(palette[influence['bone']], p)
            for axis in range(3):
                v[axis] += influence['weight'] * q[axis]
        result.append(v)
    return result


def euler_xyz(q):
    r = rotation_matrix(q)
    y = math.asin(max(-1., min(1., -r[2][0])))
    if abs(math.cos(y)) > 1e-8:
        x, z = math.atan2(r[2][1], r[2][2]), math.atan2(r[1][0], r[0][0])
    else:
        x, z = math.atan2(-r[1][2], r[1][1]), 0.
    return [math.degrees(v) for v in (x, y, z)]


def quaternion_angle(a, b):
    dot = abs(sum(x*y for x, y in zip(normalized(a), normalized(b))))
    return math.degrees(2*math.acos(min(1., dot)))


def slerp(a, b, alpha):
    a, b = normalized(a), normalized(b)
    dot = sum(x*y for x, y in zip(a, b))
    if dot < 0:
        b, dot = [-x for x in b], -dot
    if dot > .9995:
        return normalized([x + alpha*(y-x) for x, y in zip(a, b)])
    angle = math.acos(min(1., dot))
    u, v = math.sin((1-alpha)*angle)/math.sin(angle), math.sin(alpha*angle)/math.sin(angle)
    return [u*x+v*y for x, y in zip(a, b)]


def interpolate(a, b, alpha):
    return {'translation': [x+alpha*(y-x) for x, y in zip(a['translation'], b['translation'])],
            'rotation': slerp(a['rotation'], b['rotation'], alpha),
            'scale_shear': [x+alpha*(y-x) for x, y in zip(a['scale_shear'], b['scale_shear'])]}
