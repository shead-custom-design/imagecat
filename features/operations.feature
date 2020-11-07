Feature: Operations

    Scenario Outline: Test Setup
        Given an empty graph
        And a task "/sample" which outputs the <sample> sample image
        When retrieving the output image from task "/sample"
        Then the image should match the <reference> reference image

        Examples:
            | sample    | reference         |
            | chelsea   | chelsea           |


    Scenario Outline: File IO
        Given an empty graph
        And a task "/sample" which outputs the <sample> sample image
        And a task "/save" with operator save path <path>
        And links [("/sample", ("/save", "image"))]
        And a task "/load" with operator load path <path>
        When updating the task "/save"
        And retrieving the output image from task "/load"
        Then the image should match the <reference> reference image

        Examples:
            | sample    | path              | reference         |
            | chelsea   | "chelsea.exr"     | chelsea-exr       |
            | chelsea   | "chelsea.icp"     | chelsea-icp       |
            | chelsea   | "chelsea.png"     | chelsea-png       |


    Scenario: Unique Names
        Given an empty graph
        And a task "/sample" with constant value "foo"
        And a task "/sample" with constant value "bar"
        Then the graph should contain task "/sample"
        And the graph should contain task "/sample1"
        And the output from "/sample" should be "foo"
        And the output from "/sample1" should be "bar"


    Scenario Outline: colormap
        Given an empty graph
        And a task "/uniform" with operator uniform layer "L" size (128, 128) components None role Role.NONE seed 1234
        And a <color module> <palette> palette reversed: <reversed>
        And a <colormap> colormap
        And a task "/colormap" with operator colormap layers <layers>
        And links [("/uniform", ("/colormap", "image"))]
        When retrieving the output image from task "/colormap"
        Then the image should match the <reference> reference image

        Examples:
            | color module | palette      | reversed  | colormap       | layers    | reference                           |
            | basic        | "Blackbody"  | False     | linear         | "*"       | colormap-linear-basic-blackbody     |
            | brewer       | "BlueRed"    | True      | linear         | "*"       | colormap-linear-brewer-bluered      |


    Scenario: colormap default mapping
        Given an empty graph
        And a task "/uniform" with operator uniform layer "L" size (128, 128) components None role Role.NONE seed 1234
        And a task "/colormap" with operator colormap layers "*" and default mapping
        And links [("/uniform", ("/colormap", "image"))]
        When retrieving the output image from task "/colormap"
        Then the image should match the colormap-default reference image


    Scenario Outline: composite
        Given an empty graph
        And a task "/foreground" with operator fill layer "C" size [256, 128] values [0, 0, 0] components None role Role.RGB
        And a task "/background" with operator fill layer "C" size [512, 512] values [1, 0.5, 0] components None role Role.RGB
        And a task "/text" with operator text anchor "mm" fontindex 0 fontname "LeagueSpartan-SemiBold.ttf" fontsize "0.33vh" layer "A" position ("0.5vw", "0.5vh") size (256, 128) text "Imagecat!"
        And a task "/comp" with operator composite pivot <pivot> position <position> orientation <orientation>
        And links [("/foreground", ("/comp", "foreground"))]
        And links [("/background", ("/comp", "background"))]
        And links [("/text", ("/comp", "mask"))]
        When retrieving the output image from task "/comp"
        Then the image should match the <reference> reference image

        Examples:
            | pivot              | position                   | orientation | reference           |
            | ("0.5vw", "0.5vh") | ("0.5vw", "0.8vh")         | 30          | composite           |
            | ("0vw", "1vh")     | ("0vw", "1vh")             | 0           | composite-tl        |


    Scenario Outline: delete
        Given an empty graph
        And a task "/fill1" with operator fill layer "C" size (128, 128) values [0.1, 0.2, 0.3] components None role Role.RGB
        And a task "/fill2" with operator fill layer "A" size (128, 128) values [1.0] components None role Role.NONE
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
            | "C"    | (128, 128)  | (1, 0.5, 0)     | ["r", "g", "b"]  | Role.RGB  | fill-color        |
            | "vel"  | (128, 128)  | (0.0, 0.5, 1.0) | ["x", "y", "z"]  | Role.NONE | fill-vel          |


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
        And a task "/fill1" with operator fill layer "C" size (128, 128) values [0.1, 0.2, 0.3] components None role Role.RGB
        And a task "/fill2" with operator fill layer "A" size (128, 128) values [1.0] components None role Role.NONE
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
        And a task "/fill" with operator fill layer "A" size (128, 128) values [1] components ["alpha"] role Role.NONE
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


    Scenario Outline: uniform
        Given an empty graph
        And a task "/uniform" with operator uniform layer <layer> size <size> components <components> role <role> seed <seed>
        When retrieving the output image from task "/uniform"
        Then the image should match the <reference> reference image

        Examples:
            | layer  | size        | components       | role      | seed | reference         |
            | "C"    | (128, 128)  | ["r", "g", "b"]  | Role.RGB  | 1234 | uniform-color     |
            | "L"    | (128, 128)  | None             | Role.NONE | 1234 | uniform-gray      |


    Scenario: Notebook Display
        Given an empty graph
        And a task "/fill1" with operator fill layer "C" size (128, 128) values [0.1, 0.2, 0.3] components None role Role.RGB
        And a task "/text" with operator text anchor "mm" fontindex 0 fontname "LeagueSpartan-SemiBold.ttf" fontsize "0.33vh" layer "A" position ("0.5vw", "0.5vh") size (256, 128) text "Imagecat!"
        And a task "/merge" with operator merge
        And links [("/fill1", ("/merge", "image1"))]
        And links [("/text", ("/merge", "image2"))]
        When retrieving the output image from task "/merge"
        Then displaying the image in a notebook should produce a visualization


