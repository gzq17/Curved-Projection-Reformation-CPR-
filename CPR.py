import numpy as np
import SimpleITK as sitk
from PIL import Image
import math


def update_list1(size, start, P, list1, last_point):
    for i in range(-1, 2):
        for j in range(-1, 2):
            for k in range(-1, 2):
                new_x, new_y, new_z = start[0] + i, start[1] + j, start[2] + k
                if new_x >= 0 and new_x < size[0] and new_y >= 0 and new_y < size[1] and new_z >= 0 and new_z < size[2]:
                    if P[new_x, new_y, new_z] == 0:
                        if [new_x, new_y, new_z] not in list1:
                            list1.append([new_x, new_y, new_z])
                            key = str(new_x) + '+' + str(new_y) + '+' + str(new_z)
                            if key in last_point.keys():
                                print('error')
                            last_point[key] = start


def find_point_list(thin_label_name, start, end):
    thin_label = sitk.GetArrayFromImage(sitk.ReadImage(thin_label_name))
    data = thin_label.copy().astype(np.float)
    data[data < 0.005] = 0.005
    size = data.shape
    cost = 1 / data
    last_point = {}
    P = np.zeros(cost.shape)
    key = str(start[0]) + '+' + str(start[1]) + '+' + str(start[2])
    P[start[0], start[1], start[2]] = 1
    last_point[key] = [-1, -1, -1]
    list1 = []
    update_list1(size, start, P, list1, last_point)
    iter_num = 0
    while P[end[0], end[1], end[2]] == 0:
        iter_num = iter_num + 1
        if iter_num > 30000:
            print('失败')
            return
        if iter_num % 100 == 0:
            print(len(list1), len(last_point))
        cost_min = 301
        index = -1
        for i in range(0, len(list1)):
            if cost_min > cost[list1[i][0], list1[i][1], list1[i][2]]:
                cost_min = cost[list1[i][0], list1[i][1], list1[i][2]]
                index = i
        P[list1[index][0], list1[index][1], list1[index][2]] = 1
        update_list1(size, [list1[index][0], list1[index][1], list1[index][2]], P, list1, last_point)
        del list1[index]
    last = end.copy()
    path = []
    while last[0] != -1:
        path.append(last)
        last = last_point[str(last[0]) + '+' + str(last[1]) + '+' + str(last[2])]
    path_arr = np.array(path[0])[np.newaxis, :]
    for i in range(1, len(path)):
        path_arr = np.concatenate([path_arr, np.array(path[i])[np.newaxis, :]])
    np.save('path.npy', path_arr)


def cpr_process(img, path):
    y_list, p_list = [], []
    y_list.append(0)
    p_list.append(img[path[0][0], :, path[0][2]])
    for i in range(1, len(path)):
        delta_y = math.sqrt(math.pow(path[i][0] - path[i - 1][0], 2) + math.pow(path[i][2] - path[i - 1][2], 2))
        y_list.append(y_list[-1] + delta_y)
        p_list.append(img[path[i][0], :, path[i][2]])
    new_img = p_list[0][np.newaxis, :]
    for i in range(1, math.ceil(y_list[-1])):
        index = []
        for j in range(0, len(y_list)):
            if i + 1 >= y_list[j] >= i - 1:
                index.append(j)
        new_row = np.zeros((p_list[0].shape[0],))
        for j in index:
            new_row = new_row + p_list[j]
        new_row = new_row / len(index)
        new_img = np.concatenate([new_img, new_row[np.newaxis, :]])
    print(new_img.shape)
    return new_img


def cpr(img_name, center_line_name):
    img = sitk.GetArrayFromImage(sitk.ReadImage(img_name))
    path = np.load(center_line_name)
    path_b = path[0]
    path_e = path[-1]
    label = np.zeros(img.shape)
    for i in range(0, path.shape[0]):
        label[int(path[i][0]), int(path[i][1]), int(path[i][2])] = 1
    label = label.astype(np.float)
    for i in range(1, 6):
        path = np.concatenate([np.array([path_b[0] - i, path_b[1], path_b[2]])[np.newaxis, :], path], axis=0)
    for i in range(1, 6):
        path = np.concatenate([path, np.array([path_e[0] + i, path_e[1], path_e[2]])[np.newaxis, :]], axis=0)
    print(path[:, 0].max() - path[:, 0].min(), path[:, 1].max() - path[:, 1].min(), path[:, 2].max() - path[:, 2].min())
    print(img.shape)
    new_img = cpr_process(img, path)
    new_label = cpr_process(label, path)
    img_slicer = (((new_img - new_img.min()) / (new_img.max() - new_img.min())) * 255).astype(np.uint8)
    img_slicer = Image.fromarray(img_slicer)
    img_slicer = img_slicer.convert("RGB")
    img_slicer = np.array(img_slicer)
    index_label = np.where(new_label > 0.2)
    for i in range(0, len(index_label[0])):
        img_slicer[index_label[0][i], index_label[1][i]] = [255, 0, 0]
    img_slicer = Image.fromarray(img_slicer)
    img_slicer = img_slicer.transpose(Image.ROTATE_180)
    img_slicer.save('show_img.png')


if __name__ == '__main__':
    root_path = 'D:/research/work_record/Code/mydata/game_data/rotterdamCenterline/'
    process_name = '235'
    img_file = root_path + 'final_test/images/' + process_name + '.nii.gz'
    center_line = 'path.npy'
    cpr(img_file, center_line)
