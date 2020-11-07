# Copyright 2020 Timothy M. Shead
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Functionality for working with high quality color maps.
"""

import numpy

from imagecat.color import Palette, srgb_to_linear

def palette(name, reverse=False):
    """Factory for :class:`imagecat.color.Palette` instances based on a set of high quality color palettes.

    Currently, the palettes "Blockbody", "ExtendedBlackbody", "Kindlmann", and
    "ExtendedKindlemann" are supported.

    Parameters
    ----------
    name: :class:`str`, required
        The name of the palette to use.
    reverse: bool, optional
        If `True`, reverse the order of the colors.

    Returns
    -------
    palette: :class:`imagecat.color.Palette`
        Palette with the requested colors.
    """
    colors = numpy.array(palette.data[name])[:,1:]
    colors = srgb_to_linear(colors)
    return Palette(colors=colors, reverse=reverse)

palette.data = {
    "Blackbody": [
        [0.0, 0.0, 0.0, 0.0],
        [0.015873015873, 0.0497734776566, 0.0152477941455, 0.00852887312598],
        [0.031746031746, 0.084855813636, 0.0304955882911, 0.017057746252],
        [0.047619047619, 0.110596777851, 0.045468486547, 0.0255866193779],
        [0.0634920634921, 0.131828466896, 0.0581726828908, 0.0341240566996],
        [0.0793650793651, 0.15396956097, 0.0666492584387, 0.0428429968035],
        [0.0952380952381, 0.177679162416, 0.0725166219647, 0.050823629234],
        [0.111111111111, 0.201904856852, 0.0780963813824, 0.0578148506676],
        [0.126984126984, 0.22659740784, 0.0833966086871, 0.0640284471441],
        [0.142857142857, 0.251720295995, 0.0884210421079, 0.0696046995283],
        [0.15873015873, 0.277244781506, 0.0931718709304, 0.0746415380267],
        [0.174603174603, 0.303147494519, 0.0976499344002, 0.0792101025496],
        [0.190476190476, 0.329403084274, 0.101856249237, 0.0834333445488],
        [0.206349206349, 0.355973461763, 0.105794993876, 0.0876339441208],
        [0.222222222222, 0.382848034388, 0.109463756409, 0.0918462462183],
        [0.238095238095, 0.410019181885, 0.112858537428, 0.0960705967607],
        [0.253968253968, 0.437479394285, 0.115974391474, 0.100307286568],
        [0.269841269841, 0.465221354411, 0.118805374491, 0.104556559102],
        [0.285714285714, 0.493237985431, 0.12134447042, 0.108818616983],
        [0.301587301587, 0.521522475956, 0.123583494231, 0.113093627519],
        [0.31746031746, 0.550068290666, 0.125512967442, 0.117381727397],
        [0.333333333333, 0.57886917165, 0.12712196061, 0.121683026697],
        [0.349206349206, 0.607919133853, 0.128397895268, 0.125997612321],
        [0.365079365079, 0.637212456877, 0.129326295006, 0.130325550956],
        [0.380952380952, 0.666743674634, 0.129890471593, 0.134666891619],
        [0.396825396825, 0.691292894468, 0.141293283089, 0.136258919233],
        [0.412698412698, 0.706485699582, 0.170344592267, 0.132534602103],
        [0.428571428571, 0.721654217074, 0.19689465803, 0.128274044848],
        [0.444444444444, 0.736799548299, 0.221800939447, 0.12340916854],
        [0.460317460317, 0.751922741791, 0.245555262747, 0.117853905198],
        [0.47619047619, 0.767024796621, 0.268467312199, 0.111496560918],
        [0.492063492063, 0.782106665487, 0.290745094317, 0.104187424625],
        [0.507936507937, 0.797169257565, 0.312535115222, 0.0957174093272],
        [0.52380952381, 0.812213441141, 0.333944389252, 0.0857782387212],
        [0.539682539683, 0.827240046048, 0.355053366625, 0.073879942571],
        [0.555555555556, 0.842249865912, 0.375923953617, 0.0591516202944],
        [0.571428571429, 0.857243660245, 0.396604712155, 0.039717323074],
        [0.587301587302, 0.870379942456, 0.418565674041, 0.0197163850683],
        [0.603174603175, 0.874344023609, 0.446974056864, 0.0181687081555],
        [0.619047619048, 0.878025845405, 0.47466075806, 0.0167976393343],
        [0.634920634921, 0.881420328496, 0.501760962635, 0.015617018173],
        [0.650793650794, 0.884522146084, 0.528379005009, 0.0146406842395],
        [0.666666666667, 0.887325704879, 0.554597071914, 0.013882477102],
        [0.68253968254, 0.889825124527, 0.58048102161, 0.0133562363286],
        [0.698412698413, 0.892014215292, 0.606084400817, 0.0130758014873],
        [0.714285714286, 0.893886453749, 0.631451293491, 0.0130550121463],
        [0.730158730159, 0.895434956251, 0.656618388603, 0.0133077078736],
        [0.746031746032, 0.89665244983, 0.681616511604, 0.0138477282374],
        [0.761904761905, 0.897531240228, 0.706471778936, 0.0146889128057],
        [0.777777777778, 0.898063176628, 0.731206482064, 0.0158451011466],
        [0.793650793651, 0.898239612652, 0.755839773918, 0.0173301328282],
        [0.809523809524, 0.89805136309, 0.780388208579, 0.0191578474186],
        [0.825396825397, 0.897488655734, 0.804866170399, 0.0213420844859],
        [0.84126984127, 0.896541077606, 0.829286218697, 0.0238966835982],
        [0.857142857143, 0.913697911059, 0.845646813981, 0.222765707352],
        [0.873015873016, 0.929653817018, 0.862126431003, 0.33192044996],
        [0.888888888889, 0.944238596146, 0.878764667333, 0.425002143402],
        [0.904761904762, 0.957362272625, 0.895566343629, 0.511514604922],
        [0.920634920635, 0.968933860547, 0.912535569382, 0.594836247911],
        [0.936507936508, 0.978859451813, 0.929675808036, 0.676549211736],
        [0.952380952381, 0.987040267732, 0.946989936457, 0.757507161315],
        [0.968253968254, 0.993370582651, 0.964480299321, 0.838212075166],
        [0.984126984127, 0.997735414612, 0.982148758928, 0.918976236288],
        [1.0, 1.0, 1.0, 1.0],
        ],
    "ExtendedBlackbody": [
        [0.0, 0.0, 0.0, 0.0],
        [0.015873015873, 0.0410204653528, 0.0125357909278, 0.0689109347353],
        [0.031746031746, 0.0728292511021, 0.0251074193759, 0.111084701438],
        [0.047619047619, 0.0914725053853, 0.0382924505445, 0.150828141972],
        [0.0634920634921, 0.103435457753, 0.0498523739394, 0.192399506279],
        [0.0793650793651, 0.11697787554, 0.0553384939223, 0.235590084984],
        [0.0952380952381, 0.13106897058, 0.0574858157959, 0.28012851826],
        [0.111111111111, 0.14451899335, 0.0588070736298, 0.325831740794],
        [0.126984126984, 0.157365748413, 0.0592310259517, 0.372622130916],
        [0.142857142857, 0.169638222229, 0.0586571629275, 0.420432193125],
        [0.15873015873, 0.181358128671, 0.0569469344531, 0.469202864472],
        [0.174603174603, 0.192541718123, 0.053903275425, 0.518882124122],
        [0.190476190476, 0.203200974518, 0.049231841621, 0.569423844856],
        [0.206349206349, 0.213344430591, 0.0424592716177, 0.620786858997],
        [0.222222222222, 0.22885083664, 0.0323118386732, 0.667716252697],
        [0.238095238095, 0.263917734376, 0.0170229151511, 0.696700251951],
        [0.253968253968, 0.297886776896, 0.0, 0.725911289487],
        [0.269841269841, 0.331147696924, 0.0, 0.755344187716],
        [0.285714285714, 0.363946896841, 0.0, 0.784994035048],
        [0.301587301587, 0.396448879507, 0.0, 0.814856165251],
        [0.31746031746, 0.428767984311, 0.0, 0.844926138887],
        [0.333333333333, 0.460986165649, 0.0, 0.875199726605],
        [0.349206349206, 0.509059764325, 0.0, 0.874878090633],
        [0.365079365079, 0.586657040025, 0.0, 0.788483458434],
        [0.380952380952, 0.647525018598, 0.0, 0.703448899692],
        [0.396825396825, 0.697310408138, 0.0, 0.61974037226],
        [0.412698412698, 0.739133997894, 0.0, 0.53725751376],
        [0.428571428571, 0.774966161238, 0.0, 0.455769190891],
        [0.444444444444, 0.806168536879, 0.0, 0.374768042226],
        [0.460317460317, 0.833747021783, 0.0227410599117, 0.293092362571],
        [0.47619047619, 0.854040299862, 0.09354692431, 0.239815658098],
        [0.492063492063, 0.86584929908, 0.151233844244, 0.239392814342],
        [0.507936507937, 0.877555741581, 0.194962727652, 0.23874888687],
        [0.52380952381, 0.889160050233, 0.232289833256, 0.237874380272],
        [0.539682539683, 0.900662633109, 0.265865002202, 0.236758898038],
        [0.555555555556, 0.912063883111, 0.296966217671, 0.235391010074],
        [0.571428571429, 0.923364177686, 0.326317530516, 0.233758094872],
        [0.587301587302, 0.934563878629, 0.354372124996, 0.231846149973],
        [0.603174603175, 0.945663331952, 0.381433685093, 0.229639562377],
        [0.619047619048, 0.956662867807, 0.407716114152, 0.227120827894],
        [0.634920634921, 0.96756280046, 0.433375921467, 0.224270204635],
        [0.650793650794, 0.978363428298, 0.458531111592, 0.22106528053],
        [0.666666666667, 0.975483038855, 0.493783717836, 0.21455014879],
        [0.68253968254, 0.97122066712, 0.528209235633, 0.20714036059],
        [0.698412698413, 0.966451052441, 0.56138151885, 0.198927581099],
        [0.714285714286, 0.961153380556, 0.593535622168, 0.189790175914],
        [0.730158730159, 0.955305133435, 0.624849458821, 0.17956891477],
        [0.746031746032, 0.948881871951, 0.655461076484, 0.168048219356],
        [0.761904761905, 0.941856982438, 0.685479806242, 0.154923356801],
        [0.777777777778, 0.934201379395, 0.714993736449, 0.139738100068],
        [0.793650793651, 0.925883154566, 0.744074884731, 0.121752089424],
        [0.809523809524, 0.916867159951, 0.772782874939, 0.0996076368025],
        [0.825396825397, 0.907114508751, 0.801167612557, 0.0702264586709],
        [0.84126984127, 0.896581973444, 0.829271271014, 0.0241364485172],
        [0.857142857143, 0.913697911059, 0.845646813981, 0.222765707352],
        [0.873015873016, 0.929653817018, 0.862126431003, 0.33192044996],
        [0.888888888889, 0.944238596146, 0.878764667333, 0.425002143402],
        [0.904761904762, 0.957362272625, 0.895566343629, 0.511514604922],
        [0.920634920635, 0.968933860547, 0.912535569382, 0.594836247911],
        [0.936507936508, 0.978859451813, 0.929675808036, 0.676549211736],
        [0.952380952381, 0.987040267732, 0.946989936457, 0.757507161315],
        [0.968253968254, 0.993370582651, 0.964480299321, 0.838212075166],
        [0.984126984127, 0.997735414612, 0.982148758928, 0.918976236288],
        [1.0, 1.0, 1.0, 1.0],
        ],
    "Kindlmann": [
        [0.0, 0.0, 0.0, 0.0],
        [0.015873015873, 0.0671185329588, 0.00322224968401, 0.0636827982308],
        [0.031746031746, 0.107829620358, 0.00527193539053, 0.110584717909],
        [0.047619047619, 0.132822207081, 0.00761865377028, 0.158685364855],
        [0.0634920634921, 0.150658364632, 0.00977706834929, 0.204368743721],
        [0.0793650793651, 0.164513703673, 0.0117840704797, 0.246150470866],
        [0.0952380952381, 0.17635738249, 0.0136716834002, 0.287096916371],
        [0.111111111111, 0.186956701473, 0.0157459008722, 0.330140235882],
        [0.126984126984, 0.196609134947, 0.0179376087423, 0.374519096987],
        [0.142857142857, 0.2058836328, 0.0200081348995, 0.419451331093],
        [0.15873015873, 0.215553664962, 0.0221102465109, 0.463608665805],
        [0.174603174603, 0.226519452924, 0.0241216136235, 0.506117428928],
        [0.190476190476, 0.239514530077, 0.0260436809284, 0.546294801685],
        [0.206349206349, 0.250904916966, 0.0280614987688, 0.588999620164],
        [0.222222222222, 0.249817749702, 0.0308415106025, 0.646402205149],
        [0.238095238095, 0.214242447671, 0.0350037426956, 0.732877018055],
        [0.253968253968, 0.0580253778952, 0.0728643854324, 0.831022738042],
        [0.269841269841, 0.0367499971596, 0.164763702978, 0.770392363186],
        [0.285714285714, 0.0335272327849, 0.22111999029, 0.703052629353],
        [0.301587301587, 0.0307269848338, 0.262580080746, 0.640328823938],
        [0.31746031746, 0.0281909469934, 0.295692282825, 0.584878656573],
        [0.333333333333, 0.0256345140463, 0.323638967672, 0.537652138675],
        [0.349206349206, 0.0239684879129, 0.348256161303, 0.498334574679],
        [0.365079365079, 0.0224741887644, 0.370718323302, 0.466267149604],
        [0.380952380952, 0.0213578271529, 0.391778498521, 0.440286960104],
        [0.396825396825, 0.0203201805033, 0.411937775621, 0.419241969322],
        [0.412698412698, 0.0208128086974, 0.431596539161, 0.400454861389],
        [0.428571428571, 0.021854471454, 0.451151641812, 0.380313980138],
        [0.444444444444, 0.0230712391057, 0.470629535023, 0.358711501755],
        [0.460317460317, 0.0233722345904, 0.490071489565, 0.335491504837],
        [0.47619047619, 0.0249491579525, 0.509419733567, 0.310616410835],
        [0.492063492063, 0.0254113583837, 0.528747638664, 0.283789671987],
        [0.507936507937, 0.0265511754015, 0.548001432252, 0.255097177506],
        [0.52380952381, 0.0275272678001, 0.56719680403, 0.224620515107],
        [0.539682539683, 0.0288835693814, 0.586306830784, 0.193022962508],
        [0.555555555556, 0.0289206421838, 0.605358177366, 0.161427264774],
        [0.571428571429, 0.0298263835637, 0.624285254063, 0.133059337268],
        [0.587301587302, 0.0308293566636, 0.643105492554, 0.112622799332],
        [0.603174603175, 0.0316208723034, 0.661869577571, 0.102453272786],
        [0.619047619048, 0.0331152985419, 0.68067601948, 0.0949485127762],
        [0.634920634921, 0.0345435219144, 0.699700412917, 0.0699256651954],
        [0.650793650794, 0.0857184757511, 0.717719140782, 0.0342188050111],
        [0.666666666667, 0.175139323574, 0.733108825242, 0.0350250894642],
        [0.68253968254, 0.251518174426, 0.747272852278, 0.0360866952214],
        [0.698412698413, 0.32393651684, 0.760140598481, 0.0363956325921],
        [0.714285714286, 0.395075620074, 0.771599170072, 0.0373892404385],
        [0.730158730159, 0.465330965142, 0.781654750673, 0.0372943827485],
        [0.746031746032, 0.535176000781, 0.790252205312, 0.0377717872748],
        [0.761904761905, 0.604490052123, 0.797425818444, 0.037983205084],
        [0.777777777778, 0.673240541923, 0.803195625374, 0.0389751481252],
        [0.793650793651, 0.741211512026, 0.807646935033, 0.0389840587975],
        [0.809523809524, 0.809722616014, 0.810405609028, 0.0389139062698],
        [0.825396825397, 0.884677097587, 0.809315141207, 0.0422072429217],
        [0.84126984127, 0.961041572569, 0.804311591633, 0.182431699323],
        [0.857142857143, 0.976621102575, 0.813785197546, 0.509571446188],
        [0.873015873016, 0.982984770875, 0.829568990311, 0.644079693295],
        [0.888888888889, 0.987002084869, 0.848098160851, 0.728496452077],
        [0.904761904762, 0.9899438027, 0.868188821379, 0.789375598354],
        [0.920634920635, 0.992130297633, 0.889285349012, 0.837111330813],
        [0.936507936508, 0.993977903803, 0.91097796791, 0.876642196307],
        [0.952380952381, 0.995740780243, 0.932999641601, 0.91092373222],
        [0.968253968254, 0.997106329898, 0.955300428452, 0.942209465159],
        [0.984126984127, 0.998512698466, 0.977660727116, 0.971567030755],
        [1.0, 1.0, 1.0, 1.0],
        ],
    "ExtendedKindlmann": [
        [0.0, 0.0, 0.0, 0.0],
        [0.015873015873, 0.0665872190856, 0.00317348530238, 0.0660895850313],
        [0.031746031746, 0.105381244894, 0.00562454296989, 0.117187973649],
        [0.047619047619, 0.126123053183, 0.00837798019045, 0.174964238809],
        [0.0634920634921, 0.137680744083, 0.0110625831087, 0.231566300512],
        [0.0793650793651, 0.145039082102, 0.013451479997, 0.282277543576],
        [0.0952380952381, 0.152044276014, 0.0156859399984, 0.327623693074],
        [0.111111111111, 0.161138270143, 0.0176484986723, 0.369879578682],
        [0.126984126984, 0.172685805995, 0.0195648094698, 0.409048640995],
        [0.142857142857, 0.165244050347, 0.0224832200874, 0.47021606479],
        [0.15873015873, 0.0279918458412, 0.0373112977636, 0.583889898993],
        [0.174603174603, 0.0238593181565, 0.127541825162, 0.499528856699],
        [0.190476190476, 0.0202386790283, 0.173243934499, 0.422468500932],
        [0.206349206349, 0.0172147086694, 0.204326250648, 0.360918661076],
        [0.222222222222, 0.0151405787086, 0.228521481166, 0.315024556602],
        [0.238095238095, 0.0137064006539, 0.249278518333, 0.281945765499],
        [0.253968253968, 0.0130509562483, 0.268304082234, 0.257774660955],
        [0.269841269841, 0.0139459196116, 0.286752940039, 0.234259017963],
        [0.285714285714, 0.0147354562034, 0.305005386829, 0.208719146502],
        [0.301587301587, 0.0155954467859, 0.323085920627, 0.180811206659],
        [0.31746031746, 0.0164494399433, 0.341015039205, 0.150220485094],
        [0.333333333333, 0.0172595614171, 0.358784804599, 0.117294366612],
        [0.349206349206, 0.0182093863706, 0.376357630368, 0.0845231419061],
        [0.365079365079, 0.0190863651751, 0.3937190206, 0.059250497456],
        [0.380952380952, 0.0200967930623, 0.410922707788, 0.049733608345],
        [0.396825396825, 0.020763380415, 0.428313466899, 0.0314984637501],
        [0.412698412698, 0.0813196226022, 0.443521025455, 0.0212422538125],
        [0.428571428571, 0.154492186368, 0.456128474882, 0.0218404104551],
        [0.444444444444, 0.22436299475, 0.466598243329, 0.0224293240327],
        [0.460317460317, 0.293165415215, 0.474818917034, 0.0228389362808],
        [0.47619047619, 0.361087617102, 0.480786997283, 0.0230247509697],
        [0.492063492063, 0.427869336004, 0.484593045332, 0.0230890727087],
        [0.507936507937, 0.494710180878, 0.485909764738, 0.0239295955349],
        [0.52380952381, 0.571030341606, 0.481000290069, 0.027614468239],
        [0.539682539683, 0.659238616311, 0.466351530046, 0.0317364210825],
        [0.555555555556, 0.759019086035, 0.437421423072, 0.036400614635],
        [0.571428571429, 0.866948968961, 0.388363362964, 0.0413685026023],
        [0.587301587302, 0.956773664209, 0.334498978088, 0.0929916734685],
        [0.603174603175, 0.962500599909, 0.364829931363, 0.213272013492],
        [0.619047619048, 0.96531706949, 0.39732820503, 0.272635650325],
        [0.634920634921, 0.968204554641, 0.427383873897, 0.332558246158],
        [0.650793650794, 0.972456233298, 0.452132993621, 0.42362405976],
        [0.666666666667, 0.974924322329, 0.475311962572, 0.523734287229],
        [0.68253968254, 0.975989878868, 0.497598275123, 0.620461989691],
        [0.698412698413, 0.977020548467, 0.518704726869, 0.710319751135],
        [0.714285714286, 0.978023338129, 0.539236804307, 0.792434027154],
        [0.730158730159, 0.978917589225, 0.559781782268, 0.866134059622],
        [0.746031746032, 0.979938765414, 0.580626873885, 0.930969250325],
        [0.761904761905, 0.973007886008, 0.607681188528, 0.981198138945],
        [0.777777777778, 0.933324131326, 0.657798954369, 0.983583414204],
        [0.793650793651, 0.908309474089, 0.697018458541, 0.985524181948],
        [0.809523809524, 0.894668785948, 0.729537811457, 0.987056417428],
        [0.825396825397, 0.889934261241, 0.757640205324, 0.988334733592],
        [0.84126984127, 0.892048970738, 0.782727772582, 0.989640628941],
        [0.857142857143, 0.898924549826, 0.805934065795, 0.990584977084],
        [0.873015873016, 0.908996109804, 0.827911240696, 0.991685867082],
        [0.888888888889, 0.916820311909, 0.850623202421, 0.992856600763],
        [0.904761904762, 0.920183803811, 0.874775808751, 0.99393928426],
        [0.920634920635, 0.921584746406, 0.899420945982, 0.9951557335],
        [0.936507936508, 0.923619461565, 0.923730853729, 0.996269632514],
        [0.952380952381, 0.928399919483, 0.947174005275, 0.996489083038],
        [0.968253968254, 0.937779381782, 0.969167619817, 0.996973557569],
        [0.984126984127, 0.95568711212, 0.988614720577, 0.997872974429],
        [1.0, 1.0, 1.0, 1.0],
        ],
}

