"""
Functions for displaying popups in the interface.
"""

import curses

import controller

from util import panel, uiTools

def init(height = -1, width = -1):
  """
  Preparation for displaying a popup. This creates a popup with a valid
  subwindow instance. If that's successful then the curses lock is acquired
  and this returns a tuple of the...
  (popup, draw width, draw height)
  Otherwise this leaves curses unlocked and returns None.
  
  Arguments:
    height - maximum height of the popup
    width  - maximum width of the popup
  """
  
  topSize = controller.getPanel("header").getHeight()
  topSize += controller.getPanel("control").getHeight()
  
  popup = panel.Panel(controller.getScreen(), "popup", topSize, height, width)
  popup.setVisible(True)
  
  # Redraws the popup to prepare a subwindow instance. If none is spawned then
  # the panel can't be drawn (for instance, due to not being visible).
  popup.redraw(True)
  if popup.win != None:
    panel.CURSES_LOCK.acquire()
    return (popup, popup.maxX - 1, popup.maxY)
  else: return None

def finalize():
  """
  Cleans up after displaying a popup, releasing the cureses lock and redrawing
  the rest of the display.
  """
  
  controller.refresh()
  panel.CURSES_LOCK.release()

def inputPrompt(msg, initialValue = ""):
  """
  Prompts the user to enter a string on the control line (which usually
  displays the page number and basic controls).
  
  Arguments:
    msg          - message to prompt the user for input with
    initialValue - initial value of the field
  """
  
  panel.CURSES_LOCK.acquire()
  controlPanel = controller.getPanel("control")
  controlPanel.setMsg(msg)
  controlPanel.redraw(True)
  userInput = controlPanel.getstr(0, len(msg), initialValue)
  controlPanel.revertMsg()
  panel.CURSES_LOCK.release()
  return userInput

def showMsg(msg, maxWait = -1, attr = curses.A_STANDOUT):
  """
  Displays a single line message on the control line for a set time. Pressing
  any key will end the message.
  
  Arguments:
    msg     - message to be displayed to the user
    maxWait - time to show the message, indefinite if -1
    attr    - attributes with which to draw the message
  """
  
  panel.CURSES_LOCK.acquire()
  controlPanel = controller.getPanel("control")
  controlPanel.setMsg(msg, attr)
  controlPanel.redraw(True)
  
  if maxWait == -1: curses.cbreak()
  else: curses.halfdelay(maxWait * 10)
  controller.getScreen().getch()
  controlPanel.revertMsg()
  curses.halfdelay(controller.REFRESH_RATE * 10)
  panel.CURSES_LOCK.release()

def showHelpPopup():
  """
  Presents a popup with instructions for the current page's hotkeys. This
  returns the user input used to close the popup. If the popup didn't close
  properly, this is an arrow, enter, or scroll key then this returns None.
  """
  
  popup, width, height = init(9, 80)
  if not popup: return
  
  exitKey = None
  try:
    pageNum = controller.getPage()
    pagePanels = controller.getPanels(pageNum)
    
    # the first page is the only one with multiple panels, and it looks better
    # with the log entries first, so reversing the order
    pagePanels.reverse()
    
    helpOptions = []
    for entry in pagePanels:
      helpOptions += entry.getHelp()
    
    # test doing afterward in case of overwriting
    popup.win.box()
    popup.addstr(0, 0, "Page %i Commands:" % pageNum, curses.A_STANDOUT)
    
    for i in range(len(helpOptions)):
      if i / 2 >= height - 2: break
      
      # draws entries in the form '<key>: <description>[ (<selection>)]', for
      # instance...
      # u: duplicate log entries (hidden)
      key, description, selection = helpOptions[i]
      if key: description = ": " + description
      row = (i / 2) + 1
      col = 2 if i % 2 == 0 else 41
      
      popup.addstr(row, col, key, curses.A_BOLD)
      col += len(key)
      popup.addstr(row, col, description)
      col += len(description)
      
      if selection:
        popup.addstr(row, col, " (")
        popup.addstr(row, col + 2, selection, curses.A_BOLD)
        popup.addstr(row, col + 2 + len(selection), ")")
    
    # tells user to press a key if the lower left is unoccupied
    if len(helpOptions) < 13 and height == 9:
      popup.addstr(7, 2, "Press any key...")
    
    popup.win.refresh()
    curses.cbreak()
    exitKey = controller.getScreen().getch()
    curses.halfdelay(controller.REFRESH_RATE * 10)
  finally: finalize()
  
  if not uiTools.isSelectionKey(exitKey) and \
    not uiTools.isScrollKey(exitKey) and \
    not exitKey in (curses.KEY_LEFT, curses.KEY_RIGHT):
    return exitKey
  else: return None

def showSortDialog(title, options, oldSelection, optionColors):
  """
  Displays a sorting dialog of the form:
  
    Current Order: <previous selection>
    New Order: <selections made>
    
    <option 1>    <option 2>    <option 3>   Cancel
  
  Options are colored when among the "Current Order" or "New Order", but not
  when an option below them. If cancel is selected or the user presses escape
  then this returns None. Otherwise, the new ordering is provided.
  
  Arguments:
    title   - title displayed for the popup window
    options      - ordered listing of option labels
    oldSelection - current ordering
    optionColors - mappings of options to their color
  """
  
  popup, width, height = init(9, 80)
  if not popup: return
  newSelections = []  # new ordering
  
  try:
    cursorLoc = 0     # index of highlighted option
    curses.cbreak()   # wait indefinitely for key presses (no timeout)
    
    selectionOptions = list(options)
    selectionOptions.append("Cancel")
    
    while len(newSelections) < len(oldSelection):
      popup.win.erase()
      popup.win.box()
      popup.addstr(0, 0, title, curses.A_STANDOUT)
      
      _drawSortSelection(popup, 1, 2, "Current Order: ", oldSelection, optionColors)
      _drawSortSelection(popup, 2, 2, "New Order: ", newSelections, optionColors)
      
      # presents remaining options, each row having up to four options with
      # spacing of nineteen cells
      row, col = 4, 0
      for i in range(len(selectionOptions)):
        optionFormat = curses.A_STANDOUT if cursorLoc == i else curses.A_NORMAL
        popup.addstr(row, col * 19 + 2, selectionOptions[i], optionFormat)
        col += 1
        if col == 4: row, col = row + 1, 0
      
      popup.win.refresh()
      
      key = controller.getScreen().getch()
      if key == curses.KEY_LEFT:
        cursorLoc = max(0, cursorLoc - 1)
      elif key == curses.KEY_RIGHT:
        cursorLoc = min(len(selectionOptions) - 1, cursorLoc + 1)
      elif key == curses.KEY_UP:
        cursorLoc = max(0, cursorLoc - 4)
      elif key == curses.KEY_DOWN:
        cursorLoc = min(len(selectionOptions) - 1, cursorLoc + 4)
      elif uiTools.isSelectionKey(key):
        selection = selectionOptions[cursorLoc]
        
        if selection == "Cancel": break
        else:
          newSelections.append(selection)
          selectionOptions.remove(selection)
          cursorLoc = min(cursorLoc, len(selectionOptions) - 1)
      elif key == 27: break # esc - cancel
      
    curses.halfdelay(controller.REFRESH_RATE * 10) # reset normal pausing behavior
  finally: finalize()
  
  if len(newSelections) == len(oldSelection):
    return newSelections
  else: return None

def _drawSortSelection(popup, y, x, prefix, options, optionColors):
  """
  Draws a series of comma separated sort selections. The whole line is bold
  and sort options also have their specified color. Example:
  
    Current Order: Man Page Entry, Option Name, Is Default
  
  Arguments:
    popup        - panel in which to draw sort selection
    y            - vertical location
    x            - horizontal location
    prefix       - initial string description
    options      - sort options to be shown
    optionColors - mappings of options to their color
  """
  
  popup.addstr(y, x, prefix, curses.A_BOLD)
  x += len(prefix)
  
  for i in range(len(options)):
    sortType = options[i]
    sortColor = uiTools.getColor(optionColors.get(sortType, "white"))
    popup.addstr(y, x, sortType, sortColor | curses.A_BOLD)
    x += len(sortType)
    
    # comma divider between options, if this isn't the last
    if i < len(options) - 1:
      popup.addstr(y, x, ", ", curses.A_BOLD)
      x += 2

def showMenu(title, options, oldSelection):
  """
  Provides menu with options laid out in a single column. User can cancel
  selection with the escape key, in which case this proives -1. Otherwise this
  returns the index of the selection.
  
  Arguments:
    title        - title displayed for the popup window
    options      - ordered listing of options to display
    oldSelection - index of the initially selected option (uses the first
                   selection without a carrot if -1)
  """
  
  maxWidth = max([len(label) for label in options]) + 9
  popup, width, height = init(len(options) + 2, maxWidth)
  if not popup: return
  key, selection = 0, oldSelection if oldSelection != -1 else 0
  
  try:
    # hides the title of the first panel on the page
    topPanel = controller.getPanels(controller.getPage())[0]
    topPanel.setTitleVisible(False)
    topPanel.redraw(True)
    
    curses.cbreak()   # wait indefinitely for key presses (no timeout)
    
    while not uiTools.isSelectionKey(key):
      popup.win.erase()
      popup.win.box()
      popup.addstr(0, 0, title, curses.A_STANDOUT)
      
      for i in range(len(options)):
        label = options[i]
        format = curses.A_STANDOUT if i == selection else curses.A_NORMAL
        tab = "> " if i == oldSelection else "  "
        popup.addstr(i + 1, 2, tab)
        popup.addstr(i + 1, 4, " %s " % label, format)
      
      popup.win.refresh()
      
      key = controller.getScreen().getch()
      if key == curses.KEY_UP: selection = max(0, selection - 1)
      elif key == curses.KEY_DOWN: selection = min(len(options) - 1, selection + 1)
      elif key == 27: selection, key = -1, curses.KEY_ENTER # esc - cancel
      
    topPanel.setTitleVisible(True)
    curses.halfdelay(controller.REFRESH_RATE * 10) # reset normal pausing behavior
  finally: finalize()
  
  return selection
