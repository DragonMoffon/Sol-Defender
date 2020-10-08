import math


def loop(combo, start, _stop):
    for k in range(start, _stop):
        _combo = list(combo)
        _combo.append(objects_list[k])
        if len(_combo) < items:
            loop(_combo, k + 1, _stop)
        else:
            print(f"Combination: \u001b[32m{_combo}\u001b[0m")


print("How Many Objects?")
objects = int(input(":"))

print("How Many Items?")
items = int(input(":"))

objects_list = list(range(1, objects+1))
print(f"All Objects: \u001b[32m{objects_list}\u001b[0m")
print(f"All Combinations: \u001b[32m{int(math.factorial(objects) / (math.factorial(items) * math.factorial(objects - items)))}\u001b[0m")

stop = objects

loop([], 0, stop)
