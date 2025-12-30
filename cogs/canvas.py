import discord
from discord.ext import commands

from utils.embeds import EmbedBuilder, EMPTY_CHAR


class CanvasCog(commands.Cog):
    """Canvas LMS integration commands."""

    # Hardcoded course IDs (CMU specific)
    COURSE_IDS = [31318, 31146, 30417]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.canvas = bot.canvas
        self.user = self.canvas.get_current_user()
        self.courses = [self.canvas.get_course(cid) for cid in self.COURSE_IDS]

    def _create_canvas_embed(self, items, title: str, numbered: bool = False, use_name_as_field: bool = True):
        """Create an embed for Canvas items."""
        embed = EmbedBuilder.create(title=title)

        for i, item in enumerate(items, 1):
            item_str = str(item)
            if numbered:
                item_str = f"{i}. {item_str}"

            if use_name_as_field:
                embed.add_field(name=EMPTY_CHAR, value=item_str, inline=False)
            else:
                embed.add_field(name=item_str, value=EMPTY_CHAR, inline=False)

        embed.set_footer(text="Type 'Cancel' to stop")
        return embed

    @commands.command(name='canvas')
    async def canvas_command(self, ctx: commands.Context):
        """
        Browse Canvas courses, assignments, and modules.
        Interactive command with step-by-step navigation.
        """
        # Step 1: Show courses
        embed = EmbedBuilder.create(title='Courses')
        for i, course in enumerate(self.courses, 1):
            embed.add_field(
                name=EMPTY_CHAR,
                value=f"{i}. {course.course_code} {course.name}",
                inline=False
            )
        embed.set_footer(text="Type 'Cancel' to stop")

        await ctx.send(embed=embed)

        # Wait for course selection
        def check_num(m, max_val):
            if m.content.lower() == 'cancel':
                return True
            return (m.author == ctx.author and
                    m.channel == ctx.channel and
                    m.content.isdigit() and
                    1 <= int(m.content) <= max_val)

        def check_text(m):
            if m.content.lower() == 'cancel':
                return True
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for(
                'message',
                check=lambda m: check_num(m, len(self.courses)),
                timeout=60.0
            )

            if msg.content.lower() == 'cancel':
                await ctx.send("Cancelled")
                return

            course_index = int(msg.content) - 1
            course = self.courses[course_index]

            # Step 2: Ask for Assignments or Modules
            embed = EmbedBuilder.create(title=course.name)
            embed.add_field(name="'Assignments' or 'Modules'", value=EMPTY_CHAR, inline=False)
            embed.set_footer(text="Type 'Cancel' to stop")

            await ctx.send(embed=embed)

            msg = await self.bot.wait_for('message', check=check_text, timeout=60.0)

            if msg.content.lower() == 'cancel':
                await ctx.send("Cancelled")
                return

            choice = msg.content.lower()

            if choice.startswith('a') or 'assignment' in choice:
                # Show assignments
                assignments = list(course.get_assignments())
                embed = self._create_canvas_embed(assignments, course.name, numbered=True)
                await ctx.send(embed=embed)

                # Wait for assignment selection
                msg = await self.bot.wait_for(
                    'message',
                    check=lambda m: check_num(m, len(assignments)),
                    timeout=60.0
                )

                if msg.content.lower() == 'cancel':
                    await ctx.send("Cancelled")
                    return

                assignment_index = int(msg.content) - 1
                assignment = assignments[assignment_index]

                # Show assignment details
                description = assignment.description or "No description"
                # Strip HTML tags
                while '<' in description and '>' in description:
                    start = description.index('<')
                    end = description.index('>') + 1
                    description = description[:start] + description[end:]
                description = description.replace("&nbsp;", ' ').strip()

                # Truncate if too long
                if len(description) > 2000:
                    description = description[:2000] + "..."

                embed = EmbedBuilder.create(
                    title=assignment.name,
                    description=description
                )
                await ctx.send(embed=embed)

            elif choice.startswith('m') or 'module' in choice:
                # Show modules
                modules = list(course.get_modules())
                embed = self._create_canvas_embed(modules, course.name, numbered=False, use_name_as_field=True)
                embed.add_field(
                    name=EMPTY_CHAR,
                    value=f"[Canvas Link](https://canvas.cmu.edu/courses/{course.id}/modules)"
                )
                embed.remove_footer()
                await ctx.send(embed=embed)

            else:
                await ctx.send("I think something went wrong. Please try again with 'Assignments' or 'Modules'.")

        except TimeoutError:
            await ctx.send("Selection timed out")
        except Exception as e:
            await ctx.send(f"Error: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(CanvasCog(bot))
