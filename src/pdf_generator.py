"""PDF generation module for DartConnect Statistics Generator."""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

from .config import Config


class PDFGenerator:
    """Generates PDF reports from processed DartConnect statistics."""
    
    def __init__(self, config: Config, output_dir: str = "output"):
        """
        Initialize PDF generator.
        
        Args:
            config: Configuration object
            output_dir: Directory to save PDF files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        self.logger = logging.getLogger(__name__)
        
        # Add custom styles
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=colors.darkblue,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.darkgreen,
            spaceBefore=15,
            spaceAfter=10
        ))
    
    def generate_overall_report(self, data: Dict[str, Any]) -> str:
        """
        Generate the Overall PDF report (Team-by-team detailed breakdown).
        
        Args:
            data: Processed data dictionary
            
        Returns:
            Path to the generated PDF file
        """
        report_config = self.config.get_pdf_config('report1')
        filename = f"Overall-{datetime.now().strftime('%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF document in landscape orientation to fit all columns
        from reportlab.lib.pagesizes import landscape
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=landscape(letter),  # Landscape for wide table
            topMargin=0.4*inch,
            bottomMargin=0.4*inch,
            leftMargin=0.3*inch,
            rightMargin=0.3*inch
        )
        
        # Get season info from config
        season_number = self.config.get('season.number', '74th')
        season_name = self.config.get('season.name', 'Fall/Winter 2025')
        
        # Calculate current week number
        week_number = self._calculate_week_number(data)
        
        # Build content with same header format as Individual report
        content = []
        
        # Title: League name
        content.append(Paragraph(
            "Winston-Salem Sunday Night Dart League",
            ParagraphStyle('LeagueTitle', parent=self.styles['Title'], 
                          fontSize=16, alignment=1, spaceAfter=2, fontName='Helvetica-Bold')
        ))
        
        # Subtitle: Season and week
        content.append(Paragraph(
            f"{season_number} Season - {season_name} - Week {week_number}",
            ParagraphStyle('SeasonTitle', parent=self.styles['Title'], 
                          fontSize=14, alignment=1, spaceAfter=15)
        ))
        
        # Winston Division
        content.extend(self._create_overall_division_section(data, "WINSTON DIVISION"))
        
        # Page break before Salem Division
        content.append(PageBreak())
        
        # Salem Division
        content.extend(self._create_overall_division_section(data, "SALEM DIVISION"))
        
        # Build PDF
        doc.build(content)
        
        self.logger.info(f"Generated Overall report: {filepath}")
        return str(filepath)
    
    def generate_individual_report(self, data: Dict[str, Any]) -> str:
        """
        Generate the Individual PDF report (Player Performance Rankings).
        
        Args:
            data: Processed data dictionary
            
        Returns:
            Path to the generated PDF file
        """
        filename = f"Individual-{datetime.now().strftime('%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF document with letter size
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        
        # Get season info from config
        season_number = self.config.get('season.number', '73rd')
        season_name = self.config.get('season.name', 'Fall/Winter 2025')
        
        # Calculate current week number
        week_number = self._calculate_week_number(data)
        
        # Build content to match Individual-14.pdf format
        content = []
        
        # Title: League name
        content.append(Paragraph(
            "Winston-Salem Sunday Night Dart League",
            ParagraphStyle('LeagueTitle', parent=self.styles['Title'], 
                          fontSize=16, alignment=1, spaceAfter=2, fontName='Helvetica-Bold')
        ))
        
        # Subtitle: Season and week
        content.append(Paragraph(
            f"{season_number} Season - {season_name} - Week {week_number}",
            ParagraphStyle('SeasonTitle', parent=self.styles['Title'], 
                          fontSize=14, alignment=1, spaceAfter=15)
        ))
        
        # Store enhanced_data for statistics calculations and achievement extraction
        self.enhanced_data = data.get('enhanced_data', {})
        # Also store raw_data in enhanced_data for achievement extraction
        if isinstance(self.enhanced_data, dict):
            self.enhanced_data['raw_data'] = data.get('raw_data')
        
        # Winston Division
        content.extend(self._create_individual_division_section(data, "Winston"))
        
        # Page break between divisions
        content.append(PageBreak())
        
        # Salem Division
        content.extend(self._create_individual_division_section(data, "Salem"))
        
        # Footer notes
        content.extend(self._create_individual_footer())
        
        # Build PDF
        doc.build(content)
        
        self.logger.info(f"Generated Individual report: {filepath}")
        return str(filepath)
    
    def _create_individual_division_section(self, data: Dict[str, Any], division: str) -> List:
        """Create a division section for Individual report with rankings."""
        content = []
        
        # Division header
        header_color = colors.HexColor('#90EE90') if division == "Winston" else colors.HexColor('#87CEEB')
        header_table = Table([[f"{division} Division"]], colWidths=[7.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), header_color),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(header_table)
        content.append(Spacer(1, 10))
        
        # Get pre-calculated team statistics for the division
        team_stats = data.get('team_statistics', {}).get(division, [])
        all_players = [player for team in team_stats for player in team['players']]
        
        if not all_players:
            content.append(Paragraph(f"No player data available for {division} division.", self.styles['Normal']))
            return content

        # Separate players by gender (from raw_data)
        df = data.get('raw_data', pd.DataFrame())
        player_genders = df[['player_name', 'M/F']].drop_duplicates().set_index('player_name')['M/F'].to_dict()
        
        women_players = [p for p in all_players if player_genders.get(p['name']) == 'F']
        men_players = [p for p in all_players if player_genders.get(p['name']) == 'M']

        # Helper to format and sort rankings
        def get_rankings(players, category):
            player_list = []
            for p in players:
                if category == 'singles':
                    wins = p['s01_w'] + p['sc_w']
                    losses = p['s01_l'] + p['sc_l']
                    total = wins + losses
                    if total > 0:
                        win_pct = (wins / total) * 100
                        player_list.append([p['name'], wins, losses, f"{win_pct:.2f}%", win_pct])
                elif category == 'all_events':
                    total = p['total_w'] + p['total_l']
                    if total > 0:
                        win_pct = (p['total_w'] / total) * 100
                        player_list.append([p['name'], p['total_w'], p['total_l'], f"{win_pct:.2f}%", win_pct])
                elif category == 'qp':
                    if p['legs'] > 0:
                        qp_pct = (p['qps'] / p['legs']) * 100
                        player_list.append([p['name'], p['qps'], f"{qp_pct:.2f}%", qp_pct])
                elif category == 'ratings':
                    rating = float(p['rating'])
                    if rating > 0:
                        player_list.append([p['name'], f"{rating:.4f}", rating])
            
            sort_key_index = -1
            player_list.sort(key=lambda x: x[sort_key_index], reverse=True)
            return [row[:-1] for row in player_list[:5]]

        women_stats = {
            'singles': get_rankings(women_players, 'singles'),
            'all_events': get_rankings(women_players, 'all_events'),
            'qp': get_rankings(women_players, 'qp'),
            'ratings': get_rankings(women_players, 'ratings')
        }
        men_stats = {
            'singles': get_rankings(men_players, 'singles'),
            'all_events': get_rankings(men_players, 'all_events'),
            'qp': get_rankings(men_players, 'qp'),
            'ratings': get_rankings(men_players, 'ratings')
        }

        # Create 3-column layout: Singles, All Events, Quality Points
        women_row = Table([
            [self._create_category_table("Singles - Women", women_stats['singles'], ['Name', 'W', 'L', 'Win%']),
             self._create_category_table("All Events - Women", women_stats['all_events'], ['Name', 'W', 'L', 'Win%']),
             self._create_category_table("Quality Points - Women", women_stats['qp'], ['Name', "Qp's", 'QP%'])]
        ], colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
        women_row.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5)]))
        content.append(women_row)
        content.append(Spacer(1, 15))
        
        men_row = Table([
            [self._create_category_table("Singles - Men", men_stats['singles'], ['Name', 'W', 'L', 'Win%']),
             self._create_category_table("All Events - Men", men_stats['all_events'], ['Name', 'W', 'L', 'Win%']),
             self._create_category_table("Quality Points - Men", men_stats['qp'], ['Name', "Qp's", 'QP%'])]
        ], colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
        men_row.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5)]))
        content.append(men_row)
        content.append(Spacer(1, 15))
        
        # Ratings and Special QP Register row
        content.extend(self._create_ratings_and_qp_register_section(women_stats['ratings'], men_stats['ratings'], division))
        
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_category_table(self, title: str, data: List, headers: List) -> Table:
        """Create a ranking table for one category."""
        # Add title and headers
        table_data = [[title] + [''] * (len(headers) - 1)] + [headers] + data
        
        # Calculate column widths based on number of columns
        if len(headers) == 4:  # Singles/All Events
            col_widths = [1.2*inch, 0.3*inch, 0.3*inch, 0.5*inch]
        else:  # QP (3 columns)
            col_widths = [1.3*inch, 0.5*inch, 0.5*inch]
        
        table = Table(table_data, colWidths=col_widths)
        
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Title row
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),  # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFFF99')),  # Title background
            ('SPAN', (0, 0), (-1, 0)),  # Span title across all columns
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center title
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Names left-aligned
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Numbers centered
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        table.setStyle(TableStyle(style))
        return table
    
    def _create_ratings_and_qp_register_section(self, women_ratings: List, men_ratings: List, division: str) -> List:
        """Create the ratings tables and special QP register section."""
        content = []
        
        # Ratings tables (Women | Special QP Register | Men)
        women_table = self._create_ratings_table("Ratings - Women", women_ratings)
        men_table = self._create_ratings_table("Ratings - Men", men_ratings)
        special_qp = self._create_special_qp_register(division)
        
        # Create 3-column layout
        ratings_row = Table([[women_table, special_qp, men_table]], 
                           colWidths=[2.2*inch, 3.0*inch, 2.2*inch])
        ratings_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Center the special QP register
        ]))
        content.append(ratings_row)
        
        return content
    
    def _create_ratings_table(self, title: str, data: List) -> Table:
        """Create a ratings table."""
        table_data = [[title, '']] + data
        table = Table(table_data, colWidths=[1.4*inch, 0.7*inch])
        
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFFF99')),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]
        table.setStyle(TableStyle(style))
        return table
    
    def _create_special_qp_register(self, division: str) -> Table:
        """Create the Special Quality Point Register box with actual achievements."""
        # Extract achievements from data
        achievements = self._extract_special_achievements(division)

        qp_data = []

        # Style for wrapped text in cells
        achievement_style = ParagraphStyle(
            'Achievement',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.red,
            alignment=1,  # CENTER
            leading=9
        )

        # Add 180s with text wrapping
        if achievements['perfect_180s']:
            names = ', '.join([self._format_name(name, achievements['perfect_180s'][name])
                              for name in sorted(achievements['perfect_180s'].keys())])
            qp_data.append([Paragraph(f'180 - {names}', achievement_style)])

        # Add highest out
        if achievements['highest_out']:
            player, score = achievements['highest_out']
            qp_data.append([Paragraph(f'{int(score)} OUT - {self._format_name_simple(player)}', achievement_style)])

        # Add 6 Bulls with text wrapping
        if achievements['six_bulls']:
            names = ', '.join([self._format_name(name, achievements['six_bulls'][name])
                              for name in sorted(achievements['six_bulls'].keys())])
            qp_data.append([Paragraph(f'6B - {names}', achievement_style)])

        # Add 9 Hits (9+ marks) with text wrapping
        if achievements['nine_hits']:
            names = ', '.join([self._format_name(name, achievements['nine_hits'][name])
                              for name in sorted(achievements['nine_hits'].keys())])
            qp_data.append([Paragraph(f'9H - {names}', achievement_style)])

        # If no achievements, show message
        if not qp_data:
            qp_data = [[Paragraph('No special achievements yet', achievement_style)]]

        table_data = [['Special Quality Point Register']] + qp_data
        table = Table(table_data, colWidths=[2.8*inch])

        style = [
            ('FONTSIZE', (0, 0), (-1, 0), 8),  # Header font size
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFFF99')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        table.setStyle(TableStyle(style))
        return table
    
    def _extract_special_achievements(self, division: str) -> Dict:
        """Extract special achievements (180s, high outs, 6B, 9H) for a division."""
        if not hasattr(self, 'enhanced_data'):
            return {'perfect_180s': {}, 'highest_out': None, 'six_bulls': {}, 'nine_hits': {}}
        
        # Get raw data
        from src.data_processor import DataProcessor
        df = self.enhanced_data.get('raw_data') if isinstance(self.enhanced_data, dict) else None
        if df is None:
            return {'perfect_180s': {}, 'highest_out': None, 'six_bulls': {}, 'nine_hits': {}}
        
        # Filter by division
        div_df = df[df['Division'] == division]
        
        achievements = {
            'perfect_180s': {},  # {player_name: count}
            'highest_out': None,  # (player_name, score)
            'six_bulls': {},  # {player_name: count}
            'nine_hits': {}  # {player_name: count}
        }
        
        # Find 180s in 501 games
        games_501 = div_df[div_df['game_name'] == '501 SIDO']
        perfect_180s = games_501[games_501['Hi Turn'] == 180]
        for player in perfect_180s['player_name'].unique():
            count = len(perfect_180s[perfect_180s['player_name'] == player])
            achievements['perfect_180s'][player] = count
        
        # Find highest out
        outs = games_501[games_501['DO'] > 0]
        if len(outs) > 0:
            max_out = outs['DO'].max()
            player = outs[outs['DO'] == max_out].iloc[0]['player_name']
            achievements['highest_out'] = (player, max_out)
        
        # Find 6 Bulls and 9 Hits from Cricket enhanced data
        if isinstance(self.enhanced_data, dict) and 'cricket_qp_data' in self.enhanced_data:
            cricket_data = self.enhanced_data['cricket_qp_data']
            for game in cricket_data:
                for player_data in game.get('players', []):
                    player_name = player_data.get('name')
                    # Check if player is in this division (cross-reference with raw data)
                    if player_name in div_df['player_name'].values:
                        for turn in player_data.get('turn_data', []):
                            # Check for 6 bulls
                            if turn.get('bulls', 0) >= 6:
                                achievements['six_bulls'][player_name] = achievements['six_bulls'].get(player_name, 0) + 1
                            # Check for 9+ marks (9 hits)
                            if turn.get('marks', 0) >= 9:
                                achievements['nine_hits'][player_name] = achievements['nine_hits'].get(player_name, 0) + 1
        
        return achievements
    
    def _format_name(self, full_name: str, count: int) -> str:
        """Format player name for achievement display (first name + last initial + count if > 1)."""
        # Extract first name and last initial
        parts = full_name.split()
        if not parts:
            return full_name

        first_name = parts[0]
        # Get last initial if there's a last name
        display_name = f"{first_name} {parts[-1][0]}." if len(parts) > 1 else first_name

        # Add count if more than 1
        if count > 1:
            return f"{display_name}({count})"
        return display_name
    
    def _format_name_simple(self, full_name: str) -> str:
        """Format player name to first name + last initial."""
        parts = full_name.split()
        if not parts:
            return full_name

        first_name = parts[0]
        # Get last initial if there's a last name
        return f"{first_name} {parts[-1][0]}." if len(parts) > 1 else first_name
    
    def _create_individual_footer(self) -> List:
        """Create footer with calculation notes."""
        content = []
        
        footer_text = [
            "Rating is calculated by adding Total Wins x 2 divded by Total Games plus QPs divided by Total Legs",
            "QP percentage is calculated # of QP's divided by the number of games played."
        ]
        
        for text in footer_text:
            content.append(Paragraph(
                text,
                ParagraphStyle('Footer', parent=self.styles['Normal'], 
                             fontSize=8, alignment=1, spaceAfter=2)
            ))
        
        return content
    
    def _calculate_week_number(self, data: Dict[str, Any]) -> int:
        """Calculate the current week number based on match dates.
        
        The week number is calculated by finding the earliest and latest Sunday dates
        in the data and dividing by 7. Most games are played on Sundays, so we use
        the first match date as the season start (Week 1).
        """
        if 'raw_data' not in data:
            return 1
        
        df = data['raw_data']
        
        # Get all match dates from the data (column is 'game_date' after processing)
        if 'game_date' in df.columns:
            # game_date is already a datetime column, just get unique dates
            unique_dates = df['game_date'].dt.date.unique()
            
            if len(unique_dates) > 0:
                # Sort dates to get first and last
                sorted_dates = sorted(unique_dates)
                first_match_date = sorted_dates[0]  # Season start (Week 1)
                most_recent_date = sorted_dates[-1]  # Current week
                
                # Calculate the number of weeks between first and last match
                # Week 1 starts on the first match date
                from datetime import datetime
                days_diff = (most_recent_date - first_match_date).days
                week_number = (days_diff // 7) + 1  # +1 because first week is Week 1, not Week 0
                
                return max(1, week_number)  # At least week 1
        
        return 1  # Default to week 1 if we can't determine
    
    def _create_league_summary(self, data: Dict[str, Any]) -> List:
        """Create league summary section."""
        content = []
        content.append(Paragraph("League Summary", self.styles['SectionHeader']))
        
        summary = data.get('summary', {})
        league_stats = data.get('statistics', {}).get('league_statistics', {})
        
        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Games Played', str(summary.get('total_records', 'N/A'))],
            ['Total Players', str(league_stats.get('total_players', 'N/A'))],
            ['Average Score', f"{league_stats.get('average_score', 0):.2f}"],
            ['Highest Score', str(league_stats.get('highest_score', 'N/A'))],
            ['Lowest Score', str(league_stats.get('lowest_score', 'N/A'))]
        ]
        
        # Add date range if available
        date_range = summary.get('date_range', {})
        if date_range.get('start') and date_range.get('end'):
            start_date = datetime.fromisoformat(date_range['start']).strftime('%B %d, %Y')
            end_date = datetime.fromisoformat(date_range['end']).strftime('%B %d, %Y')
            summary_data.append(['Season Period', f"{start_date} - {end_date}"])
        
        table = Table(summary_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(table)
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_player_rankings(self, data: Dict[str, Any]) -> List:
        """Create player rankings section."""
        content = []
        content.append(Paragraph("Player Rankings", self.styles['SectionHeader']))
        
        rankings = data.get('derived_metrics', {}).get('rankings', {})
        
        if 'by_average' in rankings:
            content.append(Paragraph("Top 10 Players by Average Score", self.styles['Heading3']))
            
            # Get top 10 players
            top_players = rankings['by_average'].head(10)
            
            ranking_data = [['Rank', 'Player', 'Games', 'Average', 'Total Score']]
            
            for i, (player, stats) in enumerate(top_players.iterrows(), 1):
                ranking_data.append([
                    str(i),
                    player,
                    str(int(stats['games_played'])),
                    f"{stats['average_score']:.2f}",
                    str(int(stats['total_score']))
                ])
            
            table = Table(ranking_data, colWidths=[0.8*inch, 2.5*inch, 1*inch, 1*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
            content.append(Spacer(1, 20))
        
        return content
    
    def _create_statistics_tables(self, data: Dict[str, Any]) -> List:
        """Create detailed statistics tables."""
        content = []
        content.append(Paragraph("Detailed Statistics", self.styles['SectionHeader']))
        
        # Percentiles
        percentiles = data.get('derived_metrics', {}).get('percentiles', {})
        if 'score_percentiles' in percentiles:
            content.append(Paragraph("Score Percentiles", self.styles['Heading3']))
            
            perc_data = [['Percentile', 'Score']]
            for perc, score in percentiles['score_percentiles'].items():
                perc_data.append([perc, f"{score:.2f}"])
            
            table = Table(perc_data, colWidths=[2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
            content.append(Spacer(1, 20))
        
        return content
    
    def _create_team_performance_section(self, data: Dict[str, Any], division_title: str) -> List:
        """Create team performance section matching Individual-14.pdf format."""
        content = []
        
        # Division title
        content.append(Paragraph(
            division_title,
            ParagraphStyle('DivisionTitle', parent=self.styles['Heading1'], 
                          fontSize=12, alignment=0, spaceAfter=15, spaceBefore=10)
        ))
        
        # Sample teams for the division
        teams = self._get_sample_teams(division_title)
        
        for team in teams:
            content.extend(self._create_team_table(team))
            content.append(Spacer(1, 20))
        
        return content

    def _create_division_teams_table(self, teams: List[Dict]) -> List:
        """Create a single table containing all teams in the division."""
        content = []
        
        # Headers matching Overall-14.pdf
        headers_row1 = [
            '', 'Legs\nPlayed', 'Games\nPlayed', 'Games To\nQualify', 'Tournament\nEligibility',
            'S01', '', 'SC', '', 'D01', '', 'DC', '', 'Total', '', 'Win %', 'QPs', 'QP%', 'Rating'
        ]
        
        headers_row2 = [
            '', '', '', '', '',
            'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', '', '', '', ''
        ]
        
        table_data = [headers_row1, headers_row2]
        
        # Add data for each team
        for team in teams:
            # Team name row
            team_row = [team["name"]] + [''] * 18
            table_data.append(team_row)
            
            # Player rows
            for player in team["players"]:
                row = [
                    player["name"],
                    str(player["legs"]),
                    str(player["games"]),
                    str(player["qualify"]),
                    player["eligibility"],
                    str(player["s01_w"]), str(player["s01_l"]),
                    str(player["sc_w"]), str(player["sc_l"]),
                    str(player["d01_w"]), str(player["d01_l"]),
                    str(player["dc_w"]), str(player["dc_l"]),
                    str(player["total_w"]), str(player["total_l"]),
                    player["win_pct"],
                    str(player["qps"]),
                    player["qp_pct"],
                    player["rating"]
                ]
                table_data.append(row)
            
            # Empty row after each team
            table_data.append([''] * 19)
            
        # Calculate column widths
        col_widths = [
            1.0*inch,   # Name
            0.35*inch,  # Legs
            0.35*inch,  # Games
            0.35*inch,  # Qualify
            0.6*inch,   # Eligibility
            0.2*inch, 0.2*inch, # S01
            0.2*inch, 0.2*inch, # SC
            0.2*inch, 0.2*inch, # D01
            0.2*inch, 0.2*inch, # DC
            0.2*inch, 0.2*inch, # Total
            0.4*inch,   # Win %
            0.3*inch,   # QPs
            0.4*inch,   # QP%
            0.4*inch    # Rating
        ]
        
        table = Table(table_data, colWidths=col_widths, repeatRows=2)
        
        # Styling
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            
            # Span headers
            ('SPAN', (5, 0), (6, 0)),  # S01
            ('SPAN', (7, 0), (8, 0)),  # SC
            ('SPAN', (9, 0), (10, 0)), # D01
            ('SPAN', (11, 0), (12, 0)), # DC
            ('SPAN', (13, 0), (14, 0)), # Total
        ]
        
        # Apply team-specific styling
        row_index = 2
        for team in teams:
            # Team header style
            style.extend([
                ('SPAN', (0, row_index), (-1, row_index)),
                ('BACKGROUND', (0, row_index), (-1, row_index), colors.lightblue),
                ('FONTNAME', (0, row_index), (-1, row_index), 'Helvetica-Bold'),
                ('FONTSIZE', (0, row_index), (-1, row_index), 8),
                ('ALIGN', (0, row_index), (-1, row_index), 'LEFT'),
            ])
            
            # Player rows logic
            for i, player in enumerate(team["players"]):
                player_row = row_index + 1 + i
                if player["eligibility"] == "QUALIFIED":
                    style.append(('TEXTCOLOR', (4, player_row), (4, player_row), colors.green))
                else:
                    style.append(('TEXTCOLOR', (4, player_row), (4, player_row), colors.red))
            
            # Advance row index: team header + players + empty row
            row_index += 1 + len(team["players"]) + 1
            
        table.setStyle(TableStyle(style))
        content.append(table)
        
        return content
        """Get sample team data."""
        if "WINSTON" in division:
            return [
                {
                    "name": "DARK HORSE",
                    "players": [
                        {"name": "Danny Roark", "legs": 93, "games": 39, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[5,6], [5,4], [2,7], [7,3]], "totals": [19,20], "win_pct": "48.72%", 
                         "qps": 108, "qp_pct": "116.13%", "rating": "2.1356"},
                        {"name": "Jeff Maelin", "legs": 39, "games": 16, "qualify": 2, "status": "INELIGIBLE",
                         "week_results": [[1,0], [4,4], [0,3], [2,2]], "totals": [7,9], "win_pct": "43.75%", 
                         "qps": 30, "qp_pct": "76.92%", "rating": "1.6442"},
                        {"name": "Cissy Mealin", "legs": 41, "games": 18, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[4,2], [3,0], [1,4], [3,1]], "totals": [11,7], "win_pct": "61.11%", 
                         "qps": 23, "qp_pct": "56.10%", "rating": "1.7832"},
                    ]
                },
                {
                    "name": "KBTN",
                    "players": [
                        {"name": "James Shelton", "legs": 84, "games": 37, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[5,4], [6,4], [5,4], [6,3]], "totals": [22,15], "win_pct": "59.46%", 
                         "qps": 118, "qp_pct": "140.48%", "rating": "2.5940"},
                        {"name": "Ellen Lee", "legs": 58, "games": 24, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[5,3], [1,4], [7,1], [1,2]], "totals": [14,10], "win_pct": "58.33%", 
                         "qps": 26, "qp_pct": "44.83%", "rating": "1.6149"},
                    ]
                }
            ]
        else:  # SALEM DIVISION
            return [
                {
                    "name": "FLIGHT CLUB",
                    "players": [
                        {"name": "Chris Sabolcik", "legs": 35, "games": 0, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[2,3], [9,2], [5,4], [10,0]], "totals": [26,9], "win_pct": "74.29%", 
                         "qps": 29, "qp_pct": "82.86%", "rating": "2.3143"},
                        {"name": "Lin Moore", "legs": 20, "games": 0, "qualify": 0, "status": "QUALIFIED",
                         "week_results": [[4,4], [1,1], [3,3], [2,2]], "totals": [10,10], "win_pct": "50.00%", 
                         "qps": 5, "qp_pct": "25.00%", "rating": "1.2500"},
                    ]
                }
            ]
    
    def _create_team_table(self, team_data: Dict) -> List:
        """Create a team performance table."""
        content = []
        
        # Team header
        team_header = Table([[team_data["name"]]], colWidths=[7.5*inch])
        team_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        content.append(team_header)
        
        # Table headers
        headers = [
            '', 'Legs\nPlayed', 'Games\nPlayed', 'Games To\nQualify', 'Tournament\nEligibility',
            'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', 'Win %', 'QPs', 'QP%', 'Rating'
        ]
        
        # Create player rows
        table_data = [headers]
        
        for player in team_data["players"]:
            row = [
                player["name"],
                str(player["legs"]),
                str(player["games"]),
                str(player["qualify"]),
                player["status"],
            ]
            
            # Add weekly results (4 weeks of W/L pairs)
            for week_result in player["week_results"]:
                row.extend([str(week_result[0]), str(week_result[1])])
            
            # Add totals and percentages
            row.extend([
                str(player["totals"][0]),
                str(player["totals"][1]),
                player["win_pct"],
                str(player["qps"]),
                player["qp_pct"],
                player["rating"]
            ])
            
            table_data.append(row)
        
        # Add empty rows for spacing
        empty_row = [''] * len(headers)
        for _ in range(3):
            table_data.append(empty_row)
        
        # Create table with narrow columns
        col_widths = [
            1.2*inch,  # Name
            0.4*inch, 0.4*inch, 0.4*inch, 0.6*inch,  # Basic stats
            0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch,  # Weekly W/L
            0.2*inch, 0.2*inch,  # Totals W/L
            0.4*inch, 0.3*inch, 0.4*inch, 0.4*inch  # Win%, QPs, QP%, Rating
        ]
        
        table = Table(table_data, colWidths=col_widths)
        
        # Style the table
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header bold
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Numbers centered
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Names left-aligned
        ]
        
        # Highlight qualified players
        for i, player in enumerate(team_data["players"], start=1):
            if player["status"] == "QUALIFIED":
                style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
            else:
                style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgrey))
        
        table.setStyle(TableStyle(style))
        content.append(table)
        
        return content
    
    def _create_individual_performance(self, data: Dict[str, Any]) -> List:
        """Create individual player performance section."""
        content = []
        content.append(Paragraph("Individual Player Performance", self.styles['SectionHeader']))
        
        # Get player statistics
        player_stats = data.get('statistics', {}).get('player_statistics')
        if player_stats is not None:
            # Convert MultiIndex columns to flat structure for easier access
            if hasattr(player_stats.columns, 'levels'):
                # Flatten MultiIndex columns
                player_stats.columns = ['_'.join(col).strip() for col in player_stats.columns.values]
            
            # Create a comprehensive player table
            player_data = [['Player', 'Games', 'Avg Score', 'Best Score', 'Worst Score']]
            
            for player in player_stats.index[:15]:  # Top 15 players
                row_data = [player]
                
                # Try to get the data with different possible column names
                games = self._get_stat_value(player_stats, player, ['score_count', 'games', 'count'])
                avg_score = self._get_stat_value(player_stats, player, ['score_mean', 'average', 'mean'])
                max_score = self._get_stat_value(player_stats, player, ['score_max', 'max'])
                min_score = self._get_stat_value(player_stats, player, ['score_min', 'min'])
                
                row_data.extend([
                    str(int(games)) if games is not None else 'N/A',
                    f"{avg_score:.2f}" if avg_score is not None else 'N/A',
                    str(int(max_score)) if max_score is not None else 'N/A',
                    str(int(min_score)) if min_score is not None else 'N/A'
                ])
                
                player_data.append(row_data)
            
            table = Table(player_data, colWidths=[2.5*inch, 1*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
            content.append(Spacer(1, 20))
        
        return content
    
    def _get_stat_value(self, df, player, possible_columns):
        """Helper method to get statistical value from DataFrame with flexible column names."""
        for col in possible_columns:
            if col in df.columns:
                try:
                    return df.loc[player, col]
                except (KeyError, IndexError):
                    continue
        return None
    
    def _create_performance_trends(self, data: Dict[str, Any]) -> List:
        """Create performance trends section."""
        content = []
        content.append(Paragraph("Performance Trends", self.styles['SectionHeader']))
        
        trends = data.get('derived_metrics', {}).get('trends', {})
        
        if trends:
            # Create trends table
            trend_data = [['Player', 'Trend', 'Recent Avg', 'Earlier Avg', 'Improvement']]
            
            for player, trend_info in list(trends.items())[:10]:  # Top 10
                improvement = trend_info.get('improvement_rate', 0)
                trend_data.append([
                    player,
                    trend_info.get('trend_direction', 'N/A').title(),
                    f"{trend_info.get('recent_average', 0):.2f}",
                    f"{trend_info.get('earlier_average', 0):.2f}",
                    f"{improvement:+.1f}%"
                ])
            
            table = Table(trend_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
            content.append(Spacer(1, 20))
        else:
            content.append(Paragraph("No trend data available.", self.styles['Normal']))
            content.append(Spacer(1, 20))
        
        return content
    
    def _create_detailed_statistics(self, data: Dict[str, Any]) -> List:
        """Create detailed statistics section."""
        content = []
        content.append(Paragraph("Time-Based Statistics", self.styles['SectionHeader']))
        
        time_stats = data.get('statistics', {}).get('time_statistics', {})
        
        if 'recent_activity' in time_stats:
            recent = time_stats['recent_activity']
            content.append(Paragraph("Recent Activity (Last 30 Days)", self.styles['Heading3']))
            
            activity_data = [
                ['Metric', 'Value'],
                ['Total Games', str(recent.get('total_games', 0))],
                ['Active Players', str(recent.get('active_players', 0))],
                ['Games per Day', f"{recent.get('games_per_day', 0):.2f}"]
            ]
            
            table = Table(activity_data, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightsteelblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
        
        return content
    
    def _create_overall_division_section(self, data: Dict[str, Any], division_title: str) -> List:
        """Create overall division section with team tables."""
        content = []
        
        # Get pre-calculated team statistics
        team_stats = data.get('team_statistics', {})
        
        # Map division title to key (e.g., "WINSTON DIVISION" -> "Winston")
        division_key = "Winston" if "WINSTON" in division_title else "Salem"
        if division_key not in team_stats:
            for key in team_stats.keys():
                if key.lower() in division_title.lower():
                    division_key = key
                    break
        
        teams = team_stats.get(division_key, [])
        
        # Create combined table for all teams in division
        if teams:
            content.extend(self._create_division_teams_table(teams))
        else:
            content.append(Paragraph(f"No team data available for {division_title}.", self.styles['Normal']))
            
        return content
    
    def _create_division_table(self, teams: List[Dict], division_name: str) -> List:
        """Create the main division table matching Overall-14.pdf exactly."""
        content = []
        
        # Build the complete table data
        table_data = []
        
        # Header row 1: Division name (will span 2 rows) + column headers
        # Split division name into two lines for better fit
        div_name_parts = division_name.split()
        if len(div_name_parts) == 2:
            div_display = f"{div_name_parts[0]}\n{div_name_parts[1]}"
        else:
            div_display = division_name
            
        header_row1 = [
            div_display,  # Division name in first cell (will span rows)
            'Legs\nPlayed', 'Games\nPlayed', 'Games To\nQualify', 'Tournament\nEligibility',
            'S01', '', 'SC', '', 'D01', '', 'DC', '', 'Total', '', 'Win %', 'QPs', 'QP%', 'Rating'
        ]
        
        # Header row 2: W/L sub-headers
        header_row2 = [
            '',  # Empty under division name (will be merged with row 1)
            '', '', '', '',  # Empty under basic stats
            'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L',  # W/L columns
            '', '', '', ''  # Empty under final stats
        ]
        
        table_data.extend([header_row1, header_row2])
        
        # Add all teams to the table
        for team in teams:
            # Team name row (blue background)
            team_row = [team["name"]] + [''] * 18
            table_data.append(team_row)
            
            # Player rows for this team
            for player in team["players"]:
                player_row = [
                    player["name"],
                    str(player["legs"]),
                    str(player["games"]),
                    str(player["qualify"]),
                    player["eligibility"],
                    str(player["s01_w"]), str(player["s01_l"]),
                    str(player["sc_w"]), str(player["sc_l"]),
                    str(player["d01_w"]), str(player["d01_l"]),
                    str(player["dc_w"]), str(player["dc_l"]),
                    str(player["total_w"]), str(player["total_l"]),
                    player["win_pct"],
                    str(player["qps"]),
                    player["qp_pct"],
                    player["rating"]
                ]
                table_data.append(player_row)
            
            # Add one empty row for spacing between teams
            empty_row = [''] * 19
            table_data.append(empty_row)
        
        # Create the table with adjusted column widths to prevent overlap
        col_widths = [
            1.5*inch,   # Division/Name column (much wider for division name)
            0.42*inch,  # Legs Played (slightly wider)
            0.42*inch,  # Games Played (slightly wider)
            0.48*inch,  # Games To Qualify (wider)
            0.75*inch,  # Tournament Eligibility (wider to fit INELIGIBLE)
            0.28*inch, 0.28*inch,  # S01 W/L (slightly wider)
            0.28*inch, 0.28*inch,  # SC W/L
            0.28*inch, 0.28*inch,  # D01 W/L
            0.28*inch, 0.28*inch,  # DC W/L
            0.28*inch, 0.28*inch,  # Total W/L
            0.45*inch,  # Win %
            0.35*inch,  # QPs
            0.45*inch,  # QP%
            0.45*inch   # Rating
        ]
        
        table = Table(table_data, colWidths=col_widths)
        
        # Apply styling to match sample
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 6.5),  # Slightly smaller for better fit
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),  # Headers bold
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # First column left-aligned
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Numbers centered
            
            # Division name cell styling - spans 2 rows like in sample
            ('SPAN', (0, 0), (0, 1)),  # Span division name across both header rows
            ('BACKGROUND', (0, 0), (0, 1), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 1), 11),  # Larger font for division name
            ('VALIGN', (0, 0), (0, 1), 'MIDDLE'),  # Center vertically
            ('ALIGN', (0, 0), (0, 1), 'CENTER'),  # Center horizontally
            
            # Span game type headers across W/L columns
            ('SPAN', (5, 0), (6, 0)),  # S01
            ('SPAN', (7, 0), (8, 0)),  # SC
            ('SPAN', (9, 0), (10, 0)), # D01
            ('SPAN', (11, 0), (12, 0)), # DC
            ('SPAN', (13, 0), (14, 0)), # Total
        ]
        
        # Add team name row styling (blue backgrounds)
        team_row_index = 2
        for team in teams:
            # Team name row
            style.extend([
                ('SPAN', (0, team_row_index), (-1, team_row_index)),  # Span entire row
                ('BACKGROUND', (0, team_row_index), (-1, team_row_index), colors.lightblue),
                ('FONTNAME', (0, team_row_index), (-1, team_row_index), 'Helvetica-Bold'),
                ('FONTSIZE', (0, team_row_index), (-1, team_row_index), 8),  # Larger font for team names
                ('ALIGN', (0, team_row_index), (-1, team_row_index), 'LEFT'),
            ])
            
            # Color code eligibility for players
            player_start_row = team_row_index + 1
            for i, player in enumerate(team["players"]):
                player_row = player_start_row + i
                if player["eligibility"] == "QUALIFIED":
                    style.append(('TEXTCOLOR', (4, player_row), (4, player_row), colors.green))
                else:
                    style.append(('TEXTCOLOR', (4, player_row), (4, player_row), colors.red))
            
            # Move to next team (account for team name row + players + 1 empty row)
            team_row_index += 1 + len(team["players"]) + 1
        
        table.setStyle(TableStyle(style))
        content.append(table)
        
        return content
        """Create a team section table matching Overall-14.pdf format."""
        content = []
        
        # Create the main player table with proper layout structure
        # Row 1: Division name and column headers
        headers_row1 = [
            '', 'Legs\nPlayed', 'Games\nPlayed', 'Games To\nQualify', 'Tournament\nEligibility',
            'S01', '', 'SC', '', 'D01', '', 'DC', '', 'Total', '', 'Win %', 'QPs', 'QP%', 'Rating'
        ]
        
        # Row 2: Sub-headers (W/L columns)
        headers_row2 = [
            '', '', '', '', '',
            'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', '', '', '', ''
        ]
        
        # Row 3: Team name row (spans across entire width, blue background)
        team_row = [team_data["name"]] + [''] * 18
        
        table_data = [headers_row1, headers_row2, team_row]
        
        # Add player data rows
        for player in team_data["players"]:
            row = [
                player["name"],
                str(player["legs"]),
                str(player["games"]),
                str(player["qualify"]),
                player["eligibility"],
                str(player["s01_w"]), str(player["s01_l"]),
                str(player["sc_w"]), str(player["sc_l"]),
                str(player["d01_w"]), str(player["d01_l"]),
                str(player["dc_w"]), str(player["dc_l"]),
                str(player["total_w"]), str(player["total_l"]),
                player["win_pct"],
                str(player["qps"]),
                player["qp_pct"],
                player["rating"]
            ]
            table_data.append(row)
        
        # Add minimal empty rows for spacing (removed Sub/Forfeit/Default rows)
        # Just add one empty row for visual separation
        empty_row = [''] * 19
        table_data.append(empty_row)
        
        # Create table with proper column widths
        col_widths = [
            1.0*inch,   # Name/Division column (wider for division name)
            0.35*inch,  # Legs Played
            0.35*inch,  # Games Played
            0.35*inch,  # Games To Qualify
            0.6*inch,   # Tournament Eligibility
            0.2*inch, 0.2*inch,  # S01 W/L
            0.2*inch, 0.2*inch,  # SC W/L
            0.2*inch, 0.2*inch,  # D01 W/L
            0.2*inch, 0.2*inch,  # DC W/L
            0.2*inch, 0.2*inch,  # Total W/L
            0.4*inch,   # Win %
            0.3*inch,   # QPs
            0.4*inch,   # QP%
            0.4*inch    # Rating
        ]
        
        table = Table(table_data, colWidths=col_widths)
        
        # Style the table
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),  # Headers bold
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Names left-aligned
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Numbers centered
            
            # Span S01, SC, D01, DC headers across W/L columns
            ('SPAN', (5, 0), (6, 0)),  # S01 spans cols 5-6
            ('SPAN', (7, 0), (8, 0)),  # SC spans cols 7-8
            ('SPAN', (9, 0), (10, 0)), # D01 spans cols 9-10
            ('SPAN', (11, 0), (12, 0)), # DC spans cols 11-12
            ('SPAN', (13, 0), (14, 0)), # Total spans cols 13-14
            
            # Team name row styling (row 2, blue background)
            ('SPAN', (0, 2), (-1, 2)),  # Team name spans entire row
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightblue),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('ALIGN', (0, 2), (-1, 2), 'LEFT'),
        ]
        
        # Color code eligibility for player rows (starting at row 3)
        for i, player in enumerate(team_data["players"], start=3):
            if player["eligibility"] == "QUALIFIED":
                style.append(('TEXTCOLOR', (4, i), (4, i), colors.green))
            else:
                style.append(('TEXTCOLOR', (4, i), (4, i), colors.red))
        
        table.setStyle(TableStyle(style))
        content.append(table)
        
        return content
    
    def _get_sample_player_data(self, category: str) -> List[List]:
        """Generate sample player data for demonstration."""
        if "Singles - Women" in category:
            return [
                ["Megan Ferguson", "16", "4", "80.00%"],
                ["Cissy Mealin", "7", "2", "77.78%"],
                ["Jennifer Nifong", "3", "3", "50.00%"],
                ["Ellen Lee", "6", "7", "46.15%"],
                ["Lora Josey", "7", "9", "43.75%"]
            ]
        elif "All Events - Women" in category:
            return [
                ["Megan Ferguson", "33", "7", "82.50%"],
                ["Cissy Mealin", "11", "7", "61.11%"],
                ["Ellen Lee", "14", "#", "58.33%"],
                ["Jennifer Nifong", "8", "#", "44.44%"],
                ["Lora Josey", "13", "#", "40.63%"]
            ]
        elif "Quality Points - Women" in category:
            return [
                ["Megan Ferguson", "156", "162.50%"],
                ["Lora Josey", "50", "66.67%"],
                ["Cissy Mealin", "23", "56.098%"],
                ["Jennifer Nifong", "21", "53.846%"],
                ["Brooke Masten", "38", "52.778%"]
            ]
        elif "Singles - Men" in category:
            return [
                ["Mike Todd", "19", "5", "79.17%"],
                ["Shane Schantzenbach", "7", "2", "77.78%"],
                ["Eric Hale", "17", "5", "77.27%"],
                ["Joe Arsenault Sr.", "13", "4", "76.47%"],
                ["Stefano Cortese", "17", "6", "73.91%"]
            ]
        elif "All Events - Men" in category:
            return [
                ["Shane Schantzenbach", "14", "4", "77.78%"],
                ["Stefano Cortese", "35", "#", "76.09%"],
                ["Mike Todd", "33", "#", "73.33%"],
                ["Mike Richter", "31", "#", "72.09%"],
                ["Eric Hale", "31", "#", "67.39%"]
            ]
        elif "Quality Points - Men" in category:
            return [
                ["Eric Hale", "233", "204.39%"],
                ["Mike Todd", "199", "187.74%"],
                ["Stefano Cortese", "192", "182.86%"],
                ["Ed Koment", "122", "169.44%"],
                ["Ryan McCollum", "122", "169.44%"]
            ]
        else:
            return [["Player 1", "10", "5", "66.67%"], ["Player 2", "8", "7", "53.33%"]]
    
    def _create_ratings_section(self, data: Dict[str, Any], division: str) -> List:
        """Create ratings section with women and men ratings side by side."""
        content = []
        
        # Sample ratings data
        women_ratings = [
            ["Megan Ferguson", "3.2750"],
            ["Cissy Mealin", "1.7832"],
            ["Ellen Lee", "1.6149"],
            ["Lora Josey", "1.4792"],
            ["Jennifer Nifong", "1.4274"]
        ]
        
        men_ratings = [
            ["Eric Hale", "3.3917"],
            ["Stefano Cortese", "3.3503"],
            ["Mike Todd", "3.3440"],
            ["Ed Koment", "2.9203"],
            ["Shane Schantzenbach", "2.8556"]
        ]
        
        # Create tables
        women_table = self._create_ratings_table(women_ratings, "Ratings - Women")
        men_table = self._create_ratings_table(men_ratings, "Ratings - Men")
        
        # Combine tables
        combined_table = Table([[women_table, "", men_table]], 
                              colWidths=[2.3*inch, 0.4*inch, 2.3*inch])
        combined_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        content.append(combined_table)
        content.append(Spacer(1, 10))
        
        return content
    
    
    def _create_special_achievements_section(self, data: Dict[str, Any], division: str) -> List:
        """Create special achievements section."""
        content = []
        
        # Special Quality Point Register box
        special_data = [
            ["180 - Steve B, Scott W, David S(2), Eric H(2), KC, Stefano"],
            ["122 Out - Matt D"],
            ["6B - Eric H"],
            ["9H - Mike T(3), Megan(2), Ryan Mc, Mike R, Aaron"],
            ["9H - Matt M"]
        ]
        
        special_table = Table(special_data, colWidths=[4*inch])
        special_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ]))
        
        # Center the special achievements
        centered_table = Table([[special_table]], colWidths=[7*inch])
        centered_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        content.append(centered_table)
        content.append(Spacer(1, 15))
        
        return content
    
    def _create_league_summary(self, data: Dict[str, Any]) -> List:
        """Create charts for the report."""
        content = []
        content.append(PageBreak())
        content.append(Paragraph("Visual Statistics", self.styles['SectionHeader']))
        
        # Note: This is a placeholder for chart generation
        # In a full implementation, you would create actual charts using reportlab.graphics
        content.append(Paragraph(
            "Charts would be generated here showing player performance trends, "
            "score distributions, and other visual statistics.",
            self.styles['Normal']
        ))
        
        return content
