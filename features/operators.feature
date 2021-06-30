Feature: Operators

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
        And a task "/uniform" with operator uniform layer "Y" res (128, 128) role Role.LUMINANCE seed 1234
        And a <color module> <palette> palette reversed: <reversed>
        And a <colormap> colormap
        And a task "/colormap" with operator colormap inlayer <inlayer> outlayer <outlayer>
        And links [("/uniform", ("/colormap", "image"))]
        When retrieving the output image from task "/colormap"
        Then the image should match the <reference> reference image

        Examples:
            | color module | palette      | reversed  | colormap       | inlayer   | outlayer    | reference                           |
            | basic        | "Blackbody"  | False     | linear         | None      | "C"         | colormap-linear-basic-blackbody     |
            | brewer       | "BlueRed"    | True      | linear         | None      | "C"         | colormap-linear-brewer-bluered      |


    Scenario: colormap default mapping
        Given an empty graph
        And a task "/uniform" with operator uniform layer "Y" res (128, 128) role Role.LUMINANCE seed 1234
        And a task "/colormap" with operator colormap inlayer None and default mapping
        And links [("/uniform", ("/colormap", "image"))]
        When retrieving the output image from task "/colormap"
        Then the image should match the colormap-default reference image


    Scenario Outline: composite
        Given an empty graph
        And a task "/foreground" with operator fill layer "C" res [256, 128] values [0, 0, 0] role Role.RGB
        And a task "/background" with operator fill layer "C" res [512, 512] values [1, 0.5, 0] role Role.RGB
        And a task "/text" with operator text anchor "mm" fontsize "0.33h" layer "A" position ("0.5w", "0.5h") res (256, 128) string "Imagecat"
        And a task "/comp" with operator composite pivot <pivot> position <position> orientation <orientation>
        And links [("/foreground", ("/comp", "foreground"))]
        And links [("/background", ("/comp", "background"))]
        And links [("/text", ("/comp", "mask"))]
        When retrieving the output image from task "/comp"
        Then the image should match the <reference> reference image

        Examples:
            | pivot              | position                   | orientation | reference           |
            | ("0.5w", "0.5h") | ("0.5w", "0.8h")         | 30          | composite           |
            | ("0w", "1h")     | ("0w", "1h")             | 0           | composite-tl        |


    Scenario Outline: delete
        Given an empty graph
        And a task "/fill1" with operator fill layer "C" res (128, 128) values [0.1, 0.2, 0.3] role Role.RGB
        And a task "/fill2" with operator fill layer "A" res (128, 128) values [1.0] role Role.NONE
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
        And a task "/fill" with operator fill layer <layer> res <res> values <values> role <role>
        When retrieving the output image from task "/fill"
        Then the image should match the <reference> reference image

        Examples:
            | layer  | res        | values           | role               | reference          |
            | "C"    | (128, 128)  | (1, 0.5, 0)     | Role.RGB  | fill-color        |
            | "vel"  | (128, 128)  | (0.0, 0.5, 1.0) | Role.NONE | fill-vel          |


    Scenario Outline: gaussian
        Given an empty graph
        And a task "/text" with operator text anchor "mm" fontsize "0.33h" layer "A" position ("0.5w", "0.5h") res (256, 128) string "Imagecat"
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
        And a task "/fill1" with operator fill layer "C" res (128, 128) values [0.1, 0.2, 0.3] role Role.RGB
        And a task "/fill2" with operator fill layer "A" res (128, 128) values [1.0] role Role.NONE
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
        And a task "/text" with operator text anchor "mm" fontsize "0.33h" layer "A" position ("0.5w", "0.5h") res (256, 128) string "Imagecat"
        And a task "/offset" with operator offset layers <layers> offset <offset>
        And links [("/text", ("/offset", "image"))]
        When retrieving the output image from task "/offset"
        Then the image should match the <reference> reference image

        Examples:
            | layers | offset                 | reference           |
            | "*"    | (-30, 0)               | offset-x            |
            | "*"    | (0, "0.25h")          | offset-y            |


    Scenario Outline: rename
        Given an empty graph
        And a task "/fill" with operator fill layer "A" res (128, 128) values [1] role Role.NONE
        And a task "/rename" with operator rename changes <changes>
        And links [("/fill", ("/rename", "image"))]
        When retrieving the output image from task "/rename"
        Then the image should match the <reference> reference image

        Examples:
            | changes                  | reference         |
            | {"A": "mask"}            | rename            |


    Scenario Outline: dot
        Given an empty graph
        And a task "/sample" which outputs the chelsea sample image
        And a task "/dot" with operator dot inlayer <inlayer> outlayer <outlayer> outrole <outrole> matrix <matrix>
        And links [("/sample", ("/dot", "image"))]
        When retrieving the output image from task "/dot"
        Then the image should match the <reference> reference image

        Examples:
            | inlayer   | outlayer | outrole                      | matrix                         | reference    |
            | None      | "Y"      | imagecat.data.Role.LUMINANCE | [[0.33], [0.33], [0.33]]       | dot          |


    Scenario Outline: resize
        Given an empty graph
        And a task "/text" with operator text anchor "mm" fontsize "0.33h" layer "A" position ("0.5w", "0.5h") res (256, 128) string "Imagecat"
        And a task "/resize" with operator resize order <order> res <res>
        And links [("/text", ("/resize", "image"))]
        When retrieving the output image from task "/resize"
        Then the image should match the <reference> reference image

        Examples:
            | order  | res                     | reference           |
            | 3      | ((2, "w"), "2h")         | resize-cubic         |
            | 0      | ((2, "max"), (2, "min")) | resize-nearest       |


    Scenario Outline: text
        Given an empty graph
        And a task "/text" with operator text anchor <anchor> fontsize <fontsize> layer <layer> position <position> res <res> string <string>
        When retrieving the output image from task "/text"
        Then the image should match the <reference> reference image

        Examples:
            | anchor | fontsize | layer | position         | res        | string      | reference            |
            | "mm"   | "0.33h"  | "A"   | ("0.5w", "0.5h") | (256, 128) | "Imagecat" | text                 |
            | "mm"   | "0.33h"  | "A"   | ("0.5w", "0.75h")| (256, 128) | "Imagecat" | text-y-axis          |
            | "lm"   | "0.33h"  | "A"   | ("0.0w", "0.5h") | (256, 128) | "Imagecat" | text-left-align      |
            | "rm"   | "0.33h"  | "A"   | ("1.0w", "0.5h") | (256, 128) | "Imagecat" | text-right-align     |


    Scenario Outline: uniform
        Given an empty graph
        And a task "/uniform" with operator uniform layer <layer> res <res> role <role> seed <seed>
        When retrieving the output image from task "/uniform"
        Then the image should match the <reference> reference image

        Examples:
            | layer  | res         | role           | seed | reference         |
            | "C"    | (128, 128)  | Role.RGB       | 1234 | uniform-color     |
            | "Y"    | (128, 128)  | Role.LUMINANCE | 1234 | uniform-gray      |


    Scenario: Notebook Display
        Given an empty graph
        And a task "/fill1" with operator fill layer "C" res (128, 128) values [0.1, 0.2, 0.3] role Role.RGB
        And a task "/text" with operator text anchor "mm" fontsize "0.33h" layer "A" position ("0.5w", "0.5h") res (256, 128) string "Imagecat"
        And a task "/merge" with operator merge
        And links [("/fill1", ("/merge", "image1"))]
        And links [("/text", ("/merge", "image2"))]
        When retrieving the output image from task "/merge"
        Then displaying the image in a notebook should produce a visualization


