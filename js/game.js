// gameserver address
var gameHost = 'localhost';
var gamePort = 8998;

// settings
var gridColor = '#001638';
var gridSize = 25;
var FPS = 25; // frames per second
var SPEED = 300; // miliseconds taken from one point on grid to another

// controls
var NORTH = 'w';
var WEST  = 'a';
var SOUTH = 's';
var EAST  = 'd';
var dirMod = new Object;
dirMod[NORTH] = {x:0,  y:-1};
dirMod[WEST]  = {x:-1, y:0 };
dirMod[SOUTH] = {x:0,  y:1 };
dirMod[EAST]  = {x:1,  y:0 };

// Player class
function Player(name, id, startDir, gX, gY, color)
{
	this.name = name;           	// Username loaded from chat.username (string)
	this.id = id;               	// PlayerID loaded from chat.id (string)
	this.curDir = dirMod[startDir];	// Current direction of player line (object)
	this.futDir = startDir;     	// Future direction (last input from player) (char)
	this.color = color;         	// Color of player line (string)
	this.gridPos = {x:gX,y:gY}; 	// GRID position on the game board (object)
}

// GameClient class
function GameClient(playerSide, challengeID)
{
	this.ready = false;
	this.channel = new WebSocketClient(gameHost,gamePort);
	this.t = false;
	this.playerSide = playerSide;
	this.playerID = $('#canvasTopBar_'+playerSide+' span').attr('id');
	this.challengeID = challengeID;
	
	context = $("canvas")[0].getContext("2d");
	
	// paint the grid, init grid data
	this.grid = [];
	context.lineWidth = 1;
	context.strokeStyle = gridColor;
	var wmax = 800/gridSize;
	var hmax = 600/gridSize;
	for (var w=0;w<wmax;w++)
	{
		context.moveTo(w*gridSize+0.5,0.5);
		context.lineTo(w*gridSize+0.5,600.5);
		this.grid[w] = [];
		for (var h=0;h<hmax;h++)
		{
			// wall left
			if (w == 0)
			{
				context.moveTo(0.5,h*gridSize+0.5);
				context.lineTo(800.5,h*gridSize+0.5);
				// upper left corner
				if (h == 0)
					this.grid[w][h] = [-1,-1,-1,-1];
				// lower left corner
				else if (h == hmax)
					this.grid[w][h] = [-1,-1,-1,-1];
				// left wall
				else
					this.grid[w][h] = [-1,0,-1,-1];
			}
			// wall right
			else if (w == wmax)
			{
				// upper right corner
				if (h == 0)
					this.grid[w][h] = [-1,-1,-1,-1];
				// lower right corner
				else if (h == hmax)
					this.grid[w][h] = [-1,-1,-1,-1];
				// right wall
				else
					this.grid[w][h] = [-1,-1,-1,0];
			}
			// middle
			else
			{
				// upper wall
				if (h == 0)
					this.grid[w][h] = [-1,-1,0,-1];
				// lower wall
				else if (h == hmax)
					this.grid[w][h] = [0,-1,-1,-1];
				// game space
				else
					this.grid[w][h] = [0,0,0,0];
			}
		}
	}
	context.stroke();
	
	$left = $('#canvasTopBar_left span');
	$right = $('#canvasTopBar_right span');
	this.players = {							// array of players
		left : new Player($left.html(), $left.attr('id'), EAST, 2,  12, "#ff0000"),
		right : new Player($right.html(), $right.attr('id'), WEST, 30, 12, "#00ff00")
	};
	
	var t = new Date();
	this.lastOnGridXYTime = t.getTime();		// last time player lines were on a grid crossing
	
	// gfx
	this.colorset = [];							// array of player colors
	for (x in this.players)
		this.colorset.push(this.players[x].color);
	
	this.ready = true;
}
GameClient.prototype = {
	init: function()
	{
		if (this.ready)
			this.channel.send('{"cmd":"reg","challengeID":"'+this.challengeID+'","playerSide":"'+this.playerSide+'","playerID":"'+this.playerID+'"}');
		else
		{
			var mirror = this;
			setTimeout(function(){mirror.init();}, 100);
		}
	},
	
	start: function()
	{
		var t = new Date();
		console.log('start ' + t.getTime());
		var mirror = this;
		this.t = setInterval(function(){mirror.tick();}, 1000 / FPS);
	},

	stop: function()
	{
		console.log('stop');
		clearInterval(this.t);
		this.t = false;
	},
	
	eliminatePlayer: function(p)
	{
		delete this.players[p.id];
		if (Object.keys(this.players).length == 1)
		{
			this.stop();
			for (x in this.players)
				alert("Game over. Winner is " + this.players[x].name); // TODO REDO
		}
	},
	
	// draw a line to the current grid crossing point modified by an absolute value
	drawLine: function(modX, modY)
	{
		context.lineTo(p.gridPos.x * gridSize + modX + 0.5, p.gridPos.y * gridSize + modY + 0.5);
	},

	// the game loop
	tick: function()
	{
		// calculate distance travelled since last grid crossing
		var t = new Date();
		var dist = Math.round((gridSize * (t.getTime() - this.lastOnGridXYTime)) / SPEED);
		var crossedOver = (dist > gridSize);
		
		// draw player lines
		for (side in this.players)
		{
			p = this.players[side];
			
			// prepare for drawing
			context.beginPath();
			context.strokeStyle = p.color;
			context.moveTo(p.gridPos.x * gridSize + 0.5, p.gridPos.y * gridSize + 0.5);
			
			var simpleDist;
			// reached another grid crossing
			if (crossedOver)
			{
				// update grid position
				p.gridPos.x += p.curDir.x;
				p.gridPos.y += p.curDir.y;
				
				// draw a line to the next grid crossing point
				this.drawLine(0,0);
				
				// update current line direnction
				p.curDir = dirMod[p.futDir];
				
				// reduce distance to only what has been travelled into the new grid section
				simpleDist = dist - gridSize; // TODO what if its lagging so bad we travelled more than one grid crossing? make this a reductive loop
			}
			else
				simpleDist = dist;
			
			// collision detection // TODO
			
			// draw a line to current real position
			this.drawLine(p.curDir.x * simpleDist, p.curDir.y * simpleDist);
			context.stroke();
			$("#"+side+"_x").val(p.gridPos.x * gridSize + p.curDir.x * dist);
			$("#"+side+"_y").val(p.gridPos.y * gridSize + p.curDir.y * dist);
		}
		
		// update time of last grid crossing
		if (crossedOver)
		{
			t = new Date();
			this.lastOnGridXYTime = t.getTime();
		}
	},
	
	error: function(errstr)
	{
		console.log('ERROR: ' + errstr);
	},
	
	input: function(c)
	{
		var p = this.players[this.playerSide];
		if (c in dirMod && c != p.futDir && !(
			(c == SOUTH && p.curDir == dirMod[NORTH]) ||
			(c == NORTH && p.curDir == dirMod[SOUTH]) ||
			(c == WEST  && p.curDir == dirMod[EAST])  ||
			(c == EAST  && p.curDir == dirMod[WEST])  ))
		{
			p.futDir = c;
			this.channel.send('{"cmd":"'+c+'"}'); // TODO Add x and y, then the other client knows where was the turn and can back up the line of other player
		}
	},
	
	opponentInput: function(c)
	{
		var p = this.players[(this.playerSide=='left')?'right':'left'];
		p.futDir = c;
	},
	
	bind: function()
	{
		var mirror = this;
		$(document).bind('game_init',			function(e)			{mirror.init();});
		$(document).bind('game_start',			function(e)			{mirror.start();});
		//$(document).bind('game_cdup',			function(e,stage)	{mirror.countdownUpdate(stage);});
		$(document).bind('game_error',			function(e,errstr)	{mirror.error(errstr);});
		//$(document).bind('game_resetCountdown',function(e)		{mirror.resetCountdown();});
		$(document).bind('game_opponentInput',	function(e,c)		{mirror.opponentInput(c);});
		$(document).keypress(function(e){mirror.input(String.fromCharCode(e.which));});
	}
};

var gameOnMsg = function(msg)
{
	console.log("< " + msg.data);
	pMsg = jQuery.parseJSON(msg.data);
	if ('cmd' in pMsg)
	{
		if (pMsg.cmd in dirMod)
			$(document).trigger('game_opponentInput',pMsg.cmd);
		
		else if (pMsg.cmd == 'start')
			$(document).trigger('game_start');
		
		else if (pMsg.cmd == 'err')
			$(document).trigger('game_error',pMsg.errstr);
		
		else
			$(document).trigger('game_error','Unrecognised server command: ' + msg.data);
	}
	else
		$(document).trigger('game_error','Invalid server command: ' + msg.data);
};
