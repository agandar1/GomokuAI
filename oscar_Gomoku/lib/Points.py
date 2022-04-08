
test_lists_a = [0, 0, 0, 0, 1, 0, 0]
test_lists_b = [0, 0, 1, 0, 0, 0, 0]
test_lists_c = [0, 0, 0, 1, 0, 0, 0]


def type_find(range, index):
    return index + range[0]

print(type_find(range(0, 3), 2))
print(type_find(range(2, 5), 0))
print(type_find(range(1, 4), 1))

# 0-2
# 2
# 0
# 1