player_position = pyray.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
floor_position = [500,600,200,50] # Placeholder values for a single platform, will for sure be changed later

def movement():
	if pyray.is_key_down(pyray.KeyboardKey.KEY_RIGHT): # Left and Right Inputs
		player_position.x += 5
	if pyray.is_key_down(pyray.KeyboardKey.KEY_LEFT):
    	player_position.x -= 5
        
  	if pyray.check_collision_circle_rec(player_position, 50, floor_position) == True: # Check to see is the player is grounded or not
    	if pyray.is_key_pressed(pyray.KeyboardKey.KEY_SPACE):
      		player_position.y -= 150
    	else:
      		player_position.y == 0
  	else:
    	player_position.y += 2.5 # Not integrated with Pymunk gravity yet, will be updated in the near future

# The player object is currently set as a circle with the position of player_position and a radius of 50, just to be clear
