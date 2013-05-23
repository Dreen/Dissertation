function ChatClient()
{
	this.channel = new WebSocketClient(
						$('#host').val(),
						parseInt($('#port').val())
						);
	this.username;
	this.id;
	this.is_connected = false;
	this.userlist = {};
	
	this.challengerTo = this.challengedBy = this.challengeReady = this.opponentReady = this.readyTimer = this.playerSide = this.challengeID = false;
}
ChatClient.prototype = {
	write : function(msg)
	{
		if (this.is_connected)
		{
			$('#conversation').append(msg + '<br />');
			$('#conversation').scrollTop(parseInt($('#conversation').prop("scrollHeight")));
		}
	},
		
	enable : function()
	{
		this.bind();
		$('#screen_chat').css('display', 'none');
	},
	
	disable : function()
	{
		$('#screen_chat').css('display', 'block');
	},
	
	register : function()
	{
		this.is_connected = true;
		this.write('<i>*** Connected</i>');
		this.username = $('#username').val().trim();
		var prevID = readCookie('WSChatID');
		if (prevID)
			this.channel.send('{"cmd":"reg","reg":"' + this.username + '","prevID":"'+prevID+'"}');
		else
			this.channel.send('{"cmd":"reg","reg":"' + this.username + '"}');
	},

	joinroom : function(id_, restored)
	{
		this.id = id_
		if (restored)
			this.write('<i>*** Restored session with ID: ' + this.id + '</i>');
		else
		{
			createCookie('WSChatID',this.id);
			createCookie('WSChatName',this.username);
			this.write('<i>*** Registered with ID: ' + this.id + '</i>');
		}
		
		this.write('<i>*** <b>'+this.username+'</b> has joined the room</i>');
		this.channel.send('{"cmd":"list"}');
	},

	populatelist : function(users)
	{
		$('#userlist').html('');
		var mirror = this;
		for (i=0; i<users.length; i++)
		{
			var uid = users[i][0];
			var name = users[i][1];
			$('#userlist').append($('<li></li>')
				.attr('id','user.'+uid)
				.html('&lt;'+name+'&gt;')
				.css('cursor','default')
				.click(function(){mirror.challenge($(this).attr('id').replace('user.',''));}));
			this.userlist[uid] = name;
		}
		this.write('<i>*** '+users.length+' users present</i>');
		//console.log(this.userlist);
	},
	
	challenge: function(opponent)
	{
		if (opponent != this.id && !this.challengerTo && !this.challengedBy)
		{
			this.channel.send('{"cmd":"challenge","opponent":"'+opponent+'"}');
			this.challengerTo = opponent;
			var mirror = this;
			$('#screen').css('display', 'block');
			$('#challangebox')
				.html('You have challenged <b>' + this.userlist[opponent] + '</b> to a duel!<br />Awaiting response ...<br />')
				.css('display','block')
				.append($('<a href="#">Click here to cancel your challange.</a>')
					.click(function(e){mirror.challengeResponse('cancel',mirror.challengerTo); return false;})
				);
		}
	},
	
	challenged : function(opponent)
	{
		if (this.challengerTo || this.challengedBy)
			this.challengeResponse('busy',opponent);
		else
		{
			this.challengedBy = opponent;
			var mirror = this;
			$('#screen').css('display', 'block');
			$('#challangebox')
				.html('You have been challenged by <b>' + this.userlist[opponent] + '</b> to a duel!<br />What is your response?<br />')
				.css('display','block')
				.append($('<a href="#">Accept</a>')
					.click(function(e){mirror.challengeResponse('accept',mirror.challengedBy); return false;}))
				.append(' ::: ')
				.append($('<a href="#">Decline</a>')
					.click(function(e){mirror.challengeResponse('decline',mirror.challengedBy); return false;})
				);
		}
	},
	
	challengeResponse : function(response, opponent)
	{
		this.channel.send('{"cmd":"challengeResponse","opponent":"'+opponent+'","response":"'+response+'"}');
		if (response == 'cancel')
			this.write('<i>*** You withdrew your challenge.</i>');
		else if (response == 'accept')
			this.getReady(opponent);
		else if (response == 'decline')
			this.write('<i>*** You declined the challenge.</i>');
		this.challengerTo = false;
		this.challengedBy = false;
		$('#challangebox').css('display','none');
		$('#screen').css('display', 'none');
	},
	
	chResponded : function(opponent, response, challengeID)
	{
		if (response == 'busy')
			this.write('<i>*** <b>'+this.userlist[opponent]+'</b> is already in a duel.</i>');
		else if (response == 'cancel')
			this.write('<i>*** <b>'+this.userlist[opponent]+'</b> withdrew his challenge.</i>');
		else if (response == 'accept')
		{
			this.challengeID = challengeID;
			this.getReady(opponent);
		}
		else if (response == 'decline')
			this.write('<i>*** <b>'+this.userlist[opponent]+'</b> has declined your challenge.</i>');
		this.challengerTo = false;
		this.challengedBy = false;
		$('#challangebox').css('display','none');
		$('#screen').css('display', 'none');
	},
	
	getReady : function(opponent)
	{
		this.disable();
		var mirror = this;
		// if you challenged start on the left
		if (opponent == this.challengerTo)
		{
			this.playerSide = 'left';
			$('#canvasTopBar_left span').attr('id',this.id).html(this.username);
			$('#canvasTopBar_right span').attr('id',opponent).html(this.userlist[opponent]);
			$('#canvasTopBar_right input').attr('disabled','disabled');
			$(document).bind('wschat_opponentReady',function(e){$('#canvasTopBar_right input').attr('checked','checked');});
			$('#canvasTopBar_left input').click(function(e){
				mirror.channel.send('{"cmd":"challengeReady","opponent":"'+$('#canvasTopBar_right span').attr('id')+'"}');
				$(this).attr('disabled','disabled');
				mirror.challengeReady = true;
				mirror.readyTimer = setInterval(function(){mirror.startUpGame();}, 1000);
				});
		}
		// if you were challenged, start on the right
		else if (opponent == this.challengedBy)
		{
			this.playerSide = 'right';
			$('#canvasTopBar_right span').attr('id',this.id).html(this.username);
			$('#canvasTopBar_left span').attr('id',opponent).html(this.userlist[opponent]);
			$('#canvasTopBar_left input').attr('disabled','disabled');
			$(document).bind('wschat_opponentReady',function(e){$('#canvasTopBar_left input').attr('checked','checked');});
			$('#canvasTopBar_right input').click(function(e){
				mirror.channel.send('{"cmd":"challengeReady","opponent":"'+$('#canvasTopBar_left span').attr('id')+'"}');
				$(this).attr('disabled','disabled');
				mirror.challengeReady = true;
				mirror.readyTimer = setInterval(function(){mirror.startUpGame();}, 1000);
				});
		}
		$('#canvasTopBar').css('display', 'block');
		
	},
	
	chReady : function(opponent)
	{
		if (this.playerSide == 'left')
		{
			$('#canvasTopBar_right input').attr('checked','checked');
			this.opponentReady = true;
		}
		else
		{
			$('#canvasTopBar_left input').attr('checked','checked');
			this.opponentReady = true;
		}
	},
	
	chID : function(challengeID)
	{
		this.challengeID = challengeID;
	},
	
	startUpGame : function()
	{
		if (this.challengeReady && this.opponentReady && this.challengeID)
		{
			clearInterval(this.readyTimer);
			
			state = new GameClient(this.playerSide, this.challengeID);
			state.bind();
			state.channel.connect(gameOnMsg, 'game_init');
		}
	},

	onvoice : function(from, msg)
	{
		//console.log('voice ' + from + ': ' + msg);
		this.write('&lt;'+this.userlist[from]+'&gt; ' + msg);
	},

	ontalk : function()
	{
		msg = $('#bubble').val();
		this.onvoice(this.id, msg);
		this.channel.send('{"cmd":"msg","msg":"' + msg + '"}');
		$('#bubble').val('');
	},

	disconnect : function()
	{
		// dont send the drop cmd if youre last to leave
		// otherwise disconnect button just wont work
		if (this.userlist.length > 1)
			this.channel.send('{"cmd":"drop"}');
		this.channel.disconnect();
		this.write('<i>*** Disconnected</i>');
		this.is_connected = false;
	},
	
	newuser : function(uid, name)
	{
		var mirror = this;
		this.userlist[uid] = name;
		$('#userlist').append($('<li></li>')
			.attr('id','user.'+uid)
			.html('&lt;'+name+'&gt;')
			.css('cursor','default')
			.click(function(){mirror.challenge($(this).attr('id').replace('user.',''));}));
		this.write('<i>*** <b>'+name+'</b> has entered the room</i>');
	},
	
	userdropped : function(id)
	{
		this.write('<i>*** <b>'+this.userlist[id]+'</b> has left the room</i>');
		this.channel.send('{"cmd":"list"}');
	},
	
	servererror : function(errstr)
	{
		this.write('<i>*** SERVER ERROR: '+errstr+'</i>');
	},
	
	bind : function()
	{
		var mirror = this;
		$(document).bind('wschat_register',		function(e)				{mirror.register();});
		$(document).bind('wschat_joinroom',		function(e,id,restore)	{mirror.joinroom(id,restore);});
		$(document).bind('wschat_populatelist',	function(e,users)		{mirror.populatelist(users);});
		$(document).bind('wschat_onvoice',		function(e,from,msg)	{mirror.onvoice(from,msg);});
		$(document).bind('wschat_newuser',		function(e,id,user)		{mirror.newuser(id,user);});
		$(document).bind('wschat_userdropped',	function(e,id)			{mirror.userdropped(id);});
		$(document).bind('wschat_servererror',	function(e,errstr)		{mirror.servererror(errstr);});
		$(document).bind('wschat_challenged',	function(e,opponent)	{mirror.challenged(opponent);});
		$(document).bind('wschat_chResponded',	function(e,op,res,chID)	{mirror.chResponded(op,res,chID);});
		$(document).bind('wschat_chReady',		function(e,opponent)	{mirror.chReady(opponent);});
		$(document).bind('wschat_chID',			function(e,challengeID)	{mirror.chID(challengeID);});
		$(document).keypress(function(e)
		{
			//c = String.fromCharCode(e.which);
			//alert(e.which + ' ' + c);
			if (e.which == 13)
				mirror.ontalk();
		});
		$('#exitBtn').click(function(e){mirror.disconnect();});
	}
}

var chatOnMsg = function(msg)
{
	console.log("< " + msg.data);
	pMsg = jQuery.parseJSON(msg.data);
	if ('cmd' in pMsg) // TODO rewrite for command definition
	{				   // which is loaded by WebSocketClient.onJSONCmd(). missing parameters are `undefined`. This could also destinguish between optional and required, missing required would raise an error
		// Confirmation of registration from the server
		if (pMsg.cmd == 'hi')
			if ('wb' in pMsg && pMsg.wb == 'True')
				$(document).trigger('wschat_joinroom',[pMsg.id, true]);
			else
				$(document).trigger('wschat_joinroom',[pMsg.id, false]);
		
		// Response to `list` - listing of registered users
		else if (pMsg.cmd == 'listres')
			$(document).trigger('wschat_populatelist',[pMsg.userlist]);
		
		// New user entered the room
		else if (pMsg.cmd == 'new')
			$(document).trigger('wschat_newuser',[pMsg.id, pMsg.username]);
		
		// A message from another user
		else if (pMsg.cmd == 'msg')
			$(document).trigger('wschat_onvoice',[pMsg.from,pMsg.msg]);
		
		// Connection lost to another user
		else if (pMsg.cmd == 'drop')
			$(document).trigger('wschat_userdropped',pMsg.id);
		
		// Connection lost to another user
		else if (pMsg.cmd == 'err')
			$(document).trigger('wschat_servererror',pMsg.errstr);
		
		// Someone has challanged you to a fight
		else if (pMsg.cmd == 'challenge')
			$(document).trigger('wschat_challenged',pMsg.opponent);
		
		// User responds to a challenge
		else if (pMsg.cmd == 'challengeResponse')
			if (pMsg.response == 'accept')
				$(document).trigger('wschat_chResponded',[pMsg.opponent,pMsg.response,pMsg.challengeID]);
			else
				$(document).trigger('wschat_chResponded',[pMsg.opponent,pMsg.response,false]);
		
		// User indicates readiness to start the game
		else if (pMsg.cmd == 'challengeReady')
			$(document).trigger('wschat_chReady',pMsg.opponent);
		
		// User indicates readiness to start the game
		else if (pMsg.cmd == 'challengeID')
			$(document).trigger('wschat_chID',pMsg.challengeID);
		
		else
			$(document).trigger('wschat_servererror','Unrecognised server command: ' + msg.data);
	}
	else
		$(document).trigger('wschat_servererror','Invalid server command: ' + msg.data);
};