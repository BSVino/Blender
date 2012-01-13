![](http://download.blender.org/institute/logos/blenderlogo.png)

Blender, Traditional Interface
==============================

[Blender](http://blender.org) is a free open source 3D content creation suite.

This branch is my work on a "traditional" interface to Blender, that is more accessible
to users of traditional 3d art software such as Maya. Blender is rather avant-garde
and new in its user interface innovations, but personally I find a lot of its
mechanisms to be frustrating. But at the same time, Blender has a unique paradigm for
user interaction that I want to preserve. My goals are not to make Blender behave exactly
like Maya, but rather to make the interface more intuitive for new users coming from
other tools.

This source code tree fork hosted on Github is kept up to
date with the latest stable release version of Blender found on their [Source Code Download Page](http://www.blender.org/download/source-code/).

Goals
-----

Blender is a powerful tool suite for 3d artists. Along with a lot of features, a great
amount of effort was made to make Blender as fast to use as possible for a power user.
Actions in Blender take less clicks, less button presses, and less mouse movement. At
the same time, this alienates new users. My goals are:

* *Reduce unexpected behavior.* Computers have trained people that certain actions do certain things. For example, left click selects things and executes actions, while right click opens property windows. This fork will try to retain those paradigms. They may not be good paradigms for computer usage, but they are what computer users expect.
* *Reduce 'external' information required.* When learning Blender, the user should not have to go outside of Blender (to look at tutorials, etc) to learn how to operate Blender. As much as possible the user should be instructed or be able to guess at functionality.
* *Reduce modal behavior.* A keystroke should have the same result at all times and not depend on the internal state of the application. For example, the difference between Object mode and Edit mode. Many keys do different things depending on which mode the user is in. This requires users to remember the state of the application.

If you are already accustomed to Blender and you like it the way it is, then this port
is not for you. Not only that, but I don't care what you have to say about it. You like
Blender's interface the way it is? You don't think Blender should be changed? Fine, use
regular Blender. This fork is for people who _don't_ like Blender the way it is.

That said, I will be submitting every change I make to the Blender team. Who knows, maybe they will
like some of it. But I don't expect them to accept any of them. If you like a particular
feature that is in this fork, you should petition the Blender developers to include it
in the main fork. Do you have ideas on how to improve this fork? [Talk to me](mailto: jorge@lunarworkshop.com), I love ideas.

Distribution
------------

Currently I only have the ability to compile Blender on one Platform, 32 bit Windows.
If you like the work done in this fork and you want to see it on another platform,
feel free to create a build for that platform. Send it to me and I will distribute it
as well.

To-do List
----------

### Unexpected Behavior

* When the mouse is over a menu and the user clicks on another menu, it doesn't open the other menu.
* ~~Clicking on the same menu again does not close it.~~
* If a button panel is too small the user has to scroll it.
* If the user is in grab/scale/rotate mode and presses the button again, it does nothing.
* If the user holds down a grab/scale/rotate tool, letting go does not finish the task.
* There is a + to open the "n" control panel but no - to close it.
* Clicking in empty space does not unselect.
* Right click to select is default. Left click should select.
* Right click should bring up a context menu.
* Rotate around selection is not default.
* There is no drag select or touch select.
* Double click on an edge should select an edge loop.
* Python binding helpers are everywhere and irrelevant to most users.
* No BEVEL TOOL
* Right clicking does not offer delete and sometimes rename
* Primary selection color is white, invisible when dealing with white things.
* Click-dragging on an object's center sometimes moves the object behind it instead.
* No scale management with the dolly view tool. Getting closer to an object should slow it down.
* Gray out non-selected objects while in edit mode.
* Deleting an edge deletes its face too.
* Copy is broken, right clicking on a text area doesn't give a menu to copy-paste.
* Ctrl-s shouldn't prompt to overwrite.
* While the file dialog is open, pressing the X on the window should close the file dialog. (Or there should be another X)
* Saving user preferences saves over the default .blend that's loaded when you choose "new" from the menu
* Clicking a second time on an object selects the object behind it
* Selecting a poly/edge/vert in uv should highlight it in 3d and vice versa
* Complete freezeup while generating AO, non-obvious progress bar
* No highlight while hovering the mouse over a vert/edge/face/tool handle
* No way to move something in two dimensions but not a third without keyboard shortcuts
* If only one texture layer is active and it is a multiply/overlay/etc layer, don't black everything out.
* Dragging a separator all the way over does not close it.
* If the user is looking through a camera, the rotate and zoom controls should control the camera directly.
* Canceling extrude should leave the mesh unchanged and not leave duplicate geometry.

### Workflow Improvement Wishlist

* Single-button press method to switch between object selection, vertex selection, edge selection, face selection. No "Object Mode" separate from "Edit Mode"
* Place the "Mesh Tools" toolbar in floating buttons over the 3d view.
* Don't open a window when delete is pressed. Just delete whatever is selected.
* Default to GLSL mode?
* A way to cull back faces in GLSL mode
* A minimum ambient light option for GLSL mode
* Remove the need to uncheck textures when generating environment maps?
* AO maps aren't that good. Port over some of SMAK's code?
* A render from 3d view position command
* Turning off render of a lamp should stop if from lighting the 3d view.
* Overreliance on middle mouse button.
