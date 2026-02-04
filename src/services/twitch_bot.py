"""Twitch bot integration for LewtNanny
Implements IRC connection, command handling, and auto-announcements
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TwitchConfig:
    """Twitch bot configuration"""

    oauth_token: str = ""
    bot_name: str = ""
    channel: str = ""
    command_prefix: str = "!"
    cmd_info: bool = True
    cmd_commands: bool = True
    cmd_toploots: bool = True
    cmd_allreturns: bool = True
    cmd_stats: bool = False
    cmd_loadout: bool = False
    cmd_bestrun: bool = False
    cmd_worstrun: bool = False
    cmd_skills: bool = False
    announce_global: bool = True
    announce_hof: bool = True
    cooldown_info: int = 5
    cooldown_commands: int = 10


class TwitchBot:
    """Twitch IRC bot for LewtNanny"""

    def __init__(self, db_manager=None, config: TwitchConfig | None = None):
        self.db_manager = db_manager
        self.config = config or TwitchConfig()
        self.reader = None
        self.writer = None
        self.connected = False
        self.last_command_time: dict[str, datetime] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()

        logger.info("TwitchBot initialized")

    async def connect(self):
        """Connect to Twitch IRC"""
        if not self.config.oauth_token or not self.config.bot_name:
            logger.warning("Twitch credentials not configured")
            return False

        try:
            self.reader, self.writer = await asyncio.open_connection("irc.chat.twitch.tv", 6667)

            auth_msg = f"PASS oauth:{self.config.oauth_token}\r\n"
            auth_msg += f"NICK {self.config.bot_name}\r\n"
            self.writer.write(auth_msg.encode())
            await self.writer.drain()

            join_msg = f"JOIN #{self.config.channel}\r\n"
            self.writer.write(join_msg.encode())
            await self.writer.drain()

            self.connected = True
            logger.info(f"Connected to Twitch channel: {self.config.channel}")

            asyncio.create_task(self._message_reader())
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Twitch: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from Twitch IRC"""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception as e:
                logger.error(f"Error disconnecting from Twitch: {e}")

        self.connected = False
        logger.info("Disconnected from Twitch")

    async def _message_reader(self):
        """Read messages from Twitch"""
        while self.connected:
            try:
                if self.reader:
                    data = await self.reader.readline()
                    if data:
                        await self._process_message(data.decode("utf-8", errors="ignore"))
            except Exception as e:
                logger.error(f"Error reading Twitch message: {e}")
                await asyncio.sleep(1)

    async def _process_message(self, message: str):
        """Process incoming Twitch message"""
        logger.debug(f"Twitch message: {message.strip()}")

        if message.startswith("PING"):
            pong_msg = "PONG :tmi.twitch.tv\r\n"
            self.writer.write(pong_msg.encode())
            await self.writer.drain()
            return

        if "PRIVMSG" in message:
            await self._handle_privmsg(message)

    async def _handle_privmsg(self, message: str):
        """Handle PRIVMSG from Twitch"""
        try:
            parts = message.split(":", 2)
            if len(parts) < 3:
                return

            user_info = parts[1].split("!")[0]
            username = user_info.split("@")[0]
            parts[1].split("#")[1] if "#" in parts[1] else ""
            msg_content = parts[2].strip() if len(parts) > 2 else ""

            if msg_content.startswith(self.config.command_prefix):
                command = msg_content[1:].split()[0].lower()
                args = msg_content.split()[1:] if len(msg_content.split()) > 1 else []
                await self._execute_command(username, command, args)

        except Exception as e:
            logger.error(f"Error handling PRIVMSG: {e}")

    async def _execute_command(self, username: str, command: str, args: list[str]):
        """Execute a command"""
        if not self._can_execute_command(command):
            return

        self.last_command_time[command] = datetime.now()

        response = ""

        if command == "info":
            response = self._cmd_info()
        elif command == "commands":
            response = self._cmd_commands()
        elif command == "toploots":
            response = await self._cmd_toploots()
        elif command == "allreturns":
            response = await self._cmd_allreturns()
        elif command == "stats":
            response = await self._cmd_stats()
        elif command == "loadout":
            response = self._cmd_loadout()
        elif command == "bestrun":
            response = await self._cmd_bestrun()
        elif command == "worstrun":
            response = await self._cmd_worstrun()
        elif command == "skills":
            response = await self._cmd_skills()

        if response:
            await self.send_message(response)

    def _can_execute_command(self, command: str) -> bool:
        """Check if command can be executed (cooldown)"""
        if command not in self.last_command_time:
            return True

        cooldown = self.config.cooldown_info if command == "info" else self.config.cooldown_commands
        elapsed = (datetime.now() - self.last_command_time[command]).total_seconds()
        return elapsed >= cooldown

    def _cmd_info(self) -> str:
        """Handle !info command"""
        if not self.config.cmd_info:
            return ""
        return " LewtNanny tracks your Entropia Universe loot and stats! Use !commands to see available commands."

    def _cmd_commands(self) -> str:
        """Handle !commands command"""
        if not self.config.cmd_commands:
            return ""
        cmds = ["!info", "!commands", "!toploots", "!allreturns"]
        if self.config.cmd_stats:
            cmds.append("!stats")
        if self.config.cmd_loadout:
            cmds.append("!loadout")
        if self.config.cmd_bestrun:
            cmds.append("!bestrun")
        if self.config.cmd_skills:
            cmds.append("!skills")
        return f" Available commands: {' | '.join(cmds)}"

    async def _cmd_toploots(self) -> str:
        """Handle !toploots command"""
        if not self.config.cmd_toploots:
            return ""
        return " Top loots coming soon!"

    async def _cmd_allreturns(self) -> str:
        """Handle !allreturns command"""
        if not self.config.cmd_allreturns:
            return ""
        return " Return stats coming soon!"

    async def _cmd_stats(self) -> str:
        """Handle !stats command"""
        if not self.config.cmd_stats:
            return ""
        return " Current session stats coming soon!"

    def _cmd_loadout(self) -> str:
        """Handle !loadout command"""
        if not self.config.cmd_loadout:
            return ""
        return " Active loadout: Not configured"

    async def _cmd_bestrun(self) -> str:
        """Handle !bestrun command"""
        if not self.config.cmd_bestrun:
            return ""
        return " Best run stats coming soon!"

    async def _cmd_worstrun(self) -> str:
        """Handle !worstrun command"""
        if not self.config.cmd_worstrun:
            return ""
        return " Worst run stats coming soon!"

    async def _cmd_skills(self) -> str:
        """Handle !skills command"""
        if not self.config.cmd_skills:
            return ""
        return " Skill gains coming soon!"

    async def send_message(self, message: str):
        """Send a message to chat"""
        if not self.connected or not self.writer:
            return

        try:
            full_msg = f"PRIVMSG #{self.config.channel} :{message}\r\n"
            self.writer.write(full_msg.encode())
            await self.writer.drain()
            logger.debug(f"Sent message: {message}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def announce_global(self, item_name: str, value: float):
        """Announce a global in chat"""
        if not self.config.announce_global:
            return

        message = f" GLOBAL! {item_name} valued at {value:.2f} PED! Congratulations!"
        await self.send_message(message)

    async def announce_hof(self, item_name: str, value: float):
        """Announce a HOF in chat"""
        if not self.config.announce_hof:
            return

        message = f" HOF! {item_name} valued at {value:.2f} PED! Amazing!"
        await self.send_message(message)


class TwitchBotUI:
    """UI helper for Twitch bot configuration"""

    @staticmethod
    def create_config_panel():
        """Create configuration panel for Twitch settings"""
        from PyQt6.QtWidgets import (
            QCheckBox,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QVBoxLayout,
        )

        panel = QGroupBox("Twitch Bot")
        panel.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        oauth_layout = QHBoxLayout()
        oauth_layout.addWidget(QLabel("OAuth Token:"))
        oauth_input = QLineEdit()
        oauth_input.setEchoMode(QLineEdit.EchoMode.Password)
        oauth_input.setPlaceholderText("oauth:xxxxxxxxxxxxxxxx")
        oauth_layout.addWidget(oauth_input)
        layout.addLayout(oauth_layout)

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Bot Name:"))
        bot_name_input = QLineEdit()
        bot_name_input.setPlaceholderText("your_bot_username")
        name_layout.addWidget(bot_name_input)
        layout.addLayout(name_layout)

        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channel:"))
        channel_input = QLineEdit()
        channel_input.setPlaceholderText("your_channel_name")
        channel_layout.addWidget(channel_input)
        layout.addLayout(channel_layout)

        commands_group = QGroupBox("Commands")
        commands_group.setStyleSheet("""
            QGroupBox {
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        commands_layout = QVBoxLayout()

        cmd_info_cb = QCheckBox("!info")
        commands_layout.addWidget(cmd_info_cb)

        cmd_toploots_cb = QCheckBox("!toploots")
        commands_layout.addWidget(cmd_toploots_cb)

        cmd_stats_cb = QCheckBox("!stats")
        commands_layout.addWidget(cmd_stats_cb)

        commands_group.setLayout(commands_layout)
        layout.addWidget(commands_group)

        connect_btn = QPushButton("Connect")
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #9146FF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #772CE8;
            }
        """)
        layout.addWidget(connect_btn)

        panel.setLayout(layout)
        return panel
