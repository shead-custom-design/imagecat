Feature: Operations

    Scenario Outline: Test Setup
        Given an empty graph
        And a task "/sample" which outputs the <sample> sample image
        When retrieving the output image from task "/sample"
        Then the image should match the <reference> reference image

        Examples:
            | sample    | reference         |
            | chelsea   | chelsea           |


    Scenario Outline: gaussian
        Given an empty graph
        And a task "/text" with operator text anchor "mm" fontindex 0 fontname "LeagueSpartan-SemiBold.ttf" fontsize "0.33vh" layer "A" position ("0.5vw", "0.5vh") size (256, 128) text "Imagecat!"
        And a task "/gaussian" with operator gaussian radius <radius>
        And links [("/text", ("/gaussian", "image"))]
        When retrieving the output image from task "/gaussian"
        Then the image should match the <reference> reference image

        Examples:
            | radius                 | reference           |
            | ("2px", "2px")         | gaussian            |
            | (0, 5)                 | gaussian-y          |
            | ("5px", 0)             | gaussian-x          |


    @wip
    Scenario Outline: rgb2gray
        Given an empty graph
        And a task "/sample" which outputs the chelsea sample image
        And a task "/rgb2gray" with operator rgb2gray layers <layers> weights <weights>
        And links [("/sample", ("/rgb2gray", "image"))]
        When retrieving the output image from task "/rgb2gray"
        Then the image should match the <reference> reference image

        Examples:
            | layers   | weights                  | reference         |
            | "*"      | [0.33, 0.33, 0.33]       | rgb2gray          |


    Scenario Outline: scale
        Given an empty graph
        And a task "/text" with operator text anchor "mm" fontindex 0 fontname "LeagueSpartan-SemiBold.ttf" fontsize "0.33vh" layer "A" position ("0.5vw", "0.5vh") size (256, 128) text "Imagecat!"
        And a task "/scale" with operator scale order <order> size <size>
        And links [("/text", ("/scale", "image"))]
        When retrieving the output image from task "/scale"
        Then the image should match the <reference> reference image

        Examples:
            | order  | size                       | reference           |
            | 3      | ((2, "vw"), "2vh")         | scale-cubic         |
            | 0      | ((2, "vmax"), (2, "vmin")) | scale-nearest       |


    Scenario Outline: solid
        Given an empty graph
        And a task "/solid" with operator solid layer <layer> size <size> values <values> components <components> role <role>
        When retrieving the output image from task "/solid"
        Then the image should match the <reference> reference image

        Examples:
            | layer  | size        | values          | components       | role               | reference           |
            | "C"    | (128, 128)  | (1, 0.5, 0)     | ["r", "g", "b"]  | imagecat.Role.RGB  | solid-color         |
            | "vel"  | (128, 128)  | (0.0, 0.5, 1.0) | ["x", "y", "z"]  | imagecat.Role.NONE | solid-vel           |


    Scenario Outline: text
        Given an empty graph
        And a task "/text" with operator text anchor <anchor> fontindex <fontindex> fontname <fontname> fontsize <fontsize> layer <layer> position <position> size <size> text <text>
        When retrieving the output image from task "/text"
        Then the image should match the <reference> reference image

        Examples:
            | anchor | fontindex | fontname                                | fontsize | layer | position           | size       | text        | reference            |
            | "mm"   | 0         | "LeagueSpartan-SemiBold.ttf" | "0.33vh" | "A"   | ("0.5vw", "0.5vh") | (256, 128) | "Imagecat!" | text                 |
            | "lm"   | 0         | "LeagueSpartan-SemiBold.ttf" | "0.33vh" | "A"   | ("0.0vw", "0.5vh") | (256, 128) | "Imagecat!" | text-left-align      |
            | "rm"   | 0         | "LeagueSpartan-SemiBold.ttf" | "0.33vh" | "A"   | ("1.0vw", "0.5vh") | (256, 128) | "Imagecat!" | text-right-align     |

