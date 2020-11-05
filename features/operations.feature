Feature: Operations

    Scenario Outline: Test Setup
        Given an empty graph
        And a task "/sample" which outputs the <sample> sample image
        When retrieving the output image from task "/sample"
        Then the image should match the <reference> reference image

        Examples:
            | sample    | reference         |
            | chelsea   | chelsea           |


    Scenario Outline: composite
        Given an empty graph
        And a task "/foreground" with operator fill layer "C" size [256, 128] values [0, 0, 0] components None role imagecat.Role.RGB
        And a task "/background" with operator fill layer "C" size [512, 512] values [1, 0.5, 0] components None role imagecat.Role.RGB
        And a task "/text" with operator text anchor "mm" fontindex 0 fontname "LeagueSpartan-SemiBold.ttf" fontsize "0.33vh" layer "A" position ("0.5vw", "0.5vh") size (256, 128) text "Imagecat!"
        And a task "/comp" with operator composite position <position> orientation <orientation>
        And links [("/foreground", ("/comp", "foreground"))]
        And links [("/background", ("/comp", "background"))]
        And links [("/text", ("/comp", "mask"))]
        When retrieving the output image from task "/comp"
        Then the image should match the <reference> reference image

        Examples:
            | position                   | orientation | reference           |
            | ("0.5vw", "0.8vh")         | 30          | composite           |


    Scenario Outline: delete
        Given an empty graph
        And a task "/fill1" with operator fill layer "C" size (128, 128) values [0.1, 0.2, 0.3] components None role imagecat.Role.RGB
        And a task "/fill2" with operator fill layer "A" size (128, 128) values [1.0] components None role imagecat.Role.NONE
        And a task "/merge" with operator merge
        And a task "/delete" with operator delete layers <layers>
        And links [("/fill1", ("/merge", "image1"))]
        And links [("/fill2", ("/merge", "image2"))]
        And links [("/merge", ("/delete", "image"))]
        When retrieving the output image from task "/delete"
        Then the image should match the <reference> reference image

        Examples:
            | layers | reference         |
            | "A"    | delete            |


    Scenario Outline: fill
        Given an empty graph
        And a task "/fill" with operator fill layer <layer> size <size> values <values> components <components> role <role>
        When retrieving the output image from task "/fill"
        Then the image should match the <reference> reference image

        Examples:
            | layer  | size        | values          | components       | role               | reference          |
            | "C"    | (128, 128)  | (1, 0.5, 0)     | ["r", "g", "b"]  | imagecat.Role.RGB  | fill-color        |
            | "vel"  | (128, 128)  | (0.0, 0.5, 1.0) | ["x", "y", "z"]  | imagecat.Role.NONE | fill-vel          |


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


    Scenario Outline: merge
        Given an empty graph
        And a task "/fill1" with operator fill layer "C" size (128, 128) values [0.1, 0.2, 0.3] components None role imagecat.Role.RGB
        And a task "/fill2" with operator fill layer "A" size (128, 128) values [1.0] components None role imagecat.Role.NONE
        And a task "/merge" with operator merge
        And links [("/fill1", ("/merge", "image1"))]
        And links [("/fill2", ("/merge", "image2"))]
        When retrieving the output image from task "/merge"
        Then the image should match the <reference> reference image

        Examples:
            | reference         |
            | merge             |


    Scenario Outline: offset
        Given an empty graph
        And a task "/text" with operator text anchor "mm" fontindex 0 fontname "LeagueSpartan-SemiBold.ttf" fontsize "0.33vh" layer "A" position ("0.5vw", "0.5vh") size (256, 128) text "Imagecat!"
        And a task "/offset" with operator offset layers <layers> offset <offset>
        And links [("/text", ("/offset", "image"))]
        When retrieving the output image from task "/offset"
        Then the image should match the <reference> reference image

        Examples:
            | layers | offset                 | reference           |
            | "*"    | (-30, 0)               | offset-x            |
            | "*"    | (0, "0.25vh")          | offset-y            |


    Scenario Outline: rename
        Given an empty graph
        And a task "/fill" with operator fill layer "A" size (128, 128) values [1] components ["alpha"] role imagecat.Role.NONE
        And a task "/rename" with operator rename changes <changes>
        And links [("/fill", ("/rename", "image"))]
        When retrieving the output image from task "/rename"
        Then the image should match the <reference> reference image

        Examples:
            | changes                  | reference         |
            | {"A": "mask"}            | rename            |


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


    Scenario: Notebook Display
        Given an empty graph
        And a task "/fill1" with operator fill layer "C" size (128, 128) values [0.1, 0.2, 0.3] components None role imagecat.Role.RGB
        And a task "/text" with operator text anchor "mm" fontindex 0 fontname "LeagueSpartan-SemiBold.ttf" fontsize "0.33vh" layer "A" position ("0.5vw", "0.5vh") size (256, 128) text "Imagecat!"
        And a task "/merge" with operator merge
        And links [("/fill1", ("/merge", "image1"))]
        And links [("/text", ("/merge", "image2"))]
        When retrieving the output image from task "/merge"
        Then displaying the image in a notebook should produce a visualization


