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
        
        # Get player statistics for this division
        women_stats = self._extract_player_stats(data, division, 'F')
        men_stats = self._extract_player_stats(data, division, 'M')
        
        # Create 3-column layout: Singles, All Events, Quality Points
        # Women first row
        women_row = Table([
            [self._create_category_table("Singles - Women", women_stats['singles'], ['Name', 'W', 'L', 'Win%']),
             self._create_category_table("All Events - Women", women_stats['all_events'], ['Name', 'W', 'L', 'Win%']),
             self._create_category_table("Quality Points - Women", women_stats['qp'], ['Name', "Qp's", 'QP%'])]
        ], colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
        women_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        content.append(women_row)
        content.append(Spacer(1, 15))
        
        # Men second row
        men_row = Table([
            [self._create_category_table("Singles - Men", men_stats['singles'], ['Name', 'W', 'L', 'Win%']),
             self._create_category_table("All Events - Men", men_stats['all_events'], ['Name', 'W', 'L', 'Win%']),
             self._create_category_table("Quality Points - Men", men_stats['qp'], ['Name', "Qp's", 'QP%'])]
        ], colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
        men_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        content.append(men_row)
        content.append(Spacer(1, 15))
        
        # Ratings and Special QP Register row
        content.extend(self._create_ratings_and_qp_register_section(women_stats['ratings'], men_stats['ratings'], division))
        
        content.append(Spacer(1, 20))
        
        return content
    
    def _extract_player_stats(self, data: Dict[str, Any], division: str, gender: str) -> Dict:
        """Extract player statistics for a specific division and gender."""
        if 'raw_data' not in data:
            return {'singles': [], 'all_events': [], 'qp': [], 'ratings': []}
        
        df = data['raw_data']
        
        # Filter by division and gender
        division_df = df[df['Division'] == division]
        
        # Filter by gender - the column is 'M/F' in the CSV
        if gender in ['M', 'F']:
            division_df = division_df[division_df['M/F'] == gender]
        # If gender is empty string or other, still include those players
        elif gender == '':
            division_df = division_df[division_df['M/F'].isna() | (division_df['M/F'] == '')]
        
        # Calculate stats per player (Singles = PF='S', All Events = all)
        player_stats = {}
        
        for player_name in division_df['player_name'].unique():
            player_df = division_df[division_df['player_name'] == player_name]
            
            # Singles stats (PF='S')
            singles_df = player_df[player_df['PF'] == 'S']
            singles_games = self._estimate_games_played(singles_df) if len(singles_df) > 0 else 0
            singles_game_stats = self._calculate_game_specific_stats(singles_df) if len(singles_df) > 0 else {}
            singles_wins = sum([singles_game_stats.get(g, {}).get('wins', 0) for g in singles_game_stats])
            singles_losses = sum([singles_game_stats.get(g, {}).get('losses', 0) for g in singles_game_stats])
            
            # All events stats (all PF types)
            all_games = self._estimate_games_played(player_df)
            all_game_stats = self._calculate_game_specific_stats(player_df)
            all_wins = sum([all_game_stats.get(g, {}).get('wins', 0) for g in all_game_stats])
            all_losses = sum([all_game_stats.get(g, {}).get('losses', 0) for g in all_game_stats])
            
            # QPs
            total_qps = self._calculate_total_qps(player_df, player_name, self.enhanced_data)
            legs_played = len(player_df)
            
            # Rating
            if all_games > 0:
                rating = ((all_wins * 2) / all_games) + (total_qps / legs_played) if legs_played > 0 else 0
            else:
                rating = 0
            
            player_stats[player_name] = {
                'singles_wins': singles_wins,
                'singles_losses': singles_losses,
                'singles_games': singles_games,
                'all_wins': all_wins,
                'all_losses': all_losses,
                'all_games': all_games,
                'qps': total_qps,
                'legs': legs_played,
                'rating': rating
            }
        
        # Format for tables (top 5 each)
        singles_list = []
        all_events_list = []
        qp_list = []
        ratings_list = []
        
        for name, stats in player_stats.items():
            if stats['singles_games'] > 0:
                singles_win_pct = (stats['singles_wins'] / (stats['singles_wins'] + stats['singles_losses']) * 100) if (stats['singles_wins'] + stats['singles_losses']) > 0 else 0
                singles_list.append((name, stats['singles_wins'], stats['singles_losses'], singles_win_pct, singles_win_pct))
            
            if stats['all_games'] > 0:
                all_win_pct = (stats['all_wins'] / (stats['all_wins'] + stats['all_losses']) * 100) if (stats['all_wins'] + stats['all_losses']) > 0 else 0
                all_events_list.append((name, stats['all_wins'], stats['all_losses'], all_win_pct, all_win_pct))
            
            if stats['legs'] > 0:
                qp_pct = (stats['qps'] / stats['legs'] * 100)
                qp_list.append((name, stats['qps'], qp_pct, qp_pct))
            
            if stats['rating'] > 0:
                ratings_list.append((name, stats['rating'], stats['rating']))
        
        # Sort and take top 5
        singles_list.sort(key=lambda x: x[4], reverse=True)
        all_events_list.sort(key=lambda x: x[4], reverse=True)
        qp_list.sort(key=lambda x: x[3], reverse=True)
        ratings_list.sort(key=lambda x: x[2], reverse=True)
        
        return {
            'singles': [[row[0], str(row[1]), str(row[2]), f"{row[3]:.2f}%"] for row in singles_list[:5]],
            'all_events': [[row[0], str(row[1]), str(row[2]), f"{row[3]:.2f}%"] for row in all_events_list[:5]],
            'qp': [[row[0], str(row[1]), f"{row[2]:.2f}%"] for row in qp_list[:5]],
            'ratings': [[row[0], f"{row[1]:.4f}"] for row in ratings_list[:5]]
        }
    
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
        
        # Add 180s
        if achievements['perfect_180s']:
            names = ', '.join([self._format_name(name, achievements['perfect_180s'][name]) 
                              for name in sorted(achievements['perfect_180s'].keys())])
            qp_data.append([f'180 - {names}'])
        
        # Add highest out
        if achievements['highest_out']:
            player, score = achievements['highest_out']
            qp_data.append([f'{int(score)} OUT - {self._format_name_simple(player)}'])
        
        # Add 6 Bulls
        if achievements['six_bulls']:
            names = ', '.join([self._format_name(name, achievements['six_bulls'][name]) 
                              for name in sorted(achievements['six_bulls'].keys())])
            qp_data.append([f'6B - {names}'])
        
        # Add 9 Hits (9+ marks)
        if achievements['nine_hits']:
            names = ', '.join([self._format_name(name, achievements['nine_hits'][name]) 
                              for name in sorted(achievements['nine_hits'].keys())])
            qp_data.append([f'9H - {names}'])
        
        # If no achievements, show message
        if not qp_data:
            qp_data = [['No special achievements yet']]
        
        table_data = [['Special Quality Point Register']] + qp_data
        table = Table(table_data, colWidths=[2.8*inch])
        
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFFF99')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.red),  # Red text for achievements
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
        """Format player name for achievement display (first name + count if > 1)."""
        # Extract first name
        parts = full_name.split()
        first_name = parts[0] if parts else full_name
        
        # Add count if more than 1
        if count > 1:
            return f"{first_name}({count})"
        return first_name
    
    def _format_name_simple(self, full_name: str) -> str:
        """Format player name to first name only."""
        parts = full_name.split()
        return parts[0] if parts else full_name
    
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
    
    def _get_sample_teams(self, division: str) -> List[Dict]:
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
    
    def _create_overall_division_section(self, data: Dict[str, Any], division_name: str) -> List:
        """Create a division section with teams matching Overall-14.pdf format."""
        content = []
        
        # Get teams for this division
        teams = self._get_division_teams(data, division_name)
        
        if not teams:
            return content
            
        # Create one large table for the entire division
        content.extend(self._create_division_table(teams, division_name))
        
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
    
    def _get_division_teams(self, data: Dict[str, Any], division_name: str) -> List[Dict]:
        """Get teams for a specific division from processed data."""
        if 'raw_data' not in data:
            return []
        
        # Store enhanced_data for QP calculations
        self.enhanced_data = data.get('enhanced_data', {})
        
        df = data['raw_data']
        
        # Map division names
        division_map = {
            "WINSTON DIVISION": "Winston",
            "SALEM DIVISION": "Salem"
        }
        
        target_division = division_map.get(division_name, division_name)
        
        # Get teams for this division, sorted alphabetically
        division_teams = sorted(df[df['Division'] == target_division]['Team'].unique())
        
        # Calculate games to qualify for this division
        # Round robin: each team plays every other team twice
        # Games to qualify = (number of matches) × 1.5
        num_teams = len(division_teams)
        matches_per_team = (num_teams - 1) * 2  # Play each other team twice
        games_to_qualify = int(matches_per_team * 1.5)
        
        teams = []
        for team_name in division_teams:
            team_data = self._extract_team_data(df, team_name, games_to_qualify)
            teams.append(team_data)
        
        return teams
    
    def _extract_team_data(self, df, team_name: str, games_to_qualify: int) -> Dict:
        """Extract team and player data from the DataFrame."""
        team_df = df[df['Team'] == team_name]
        
        # Get unique players for this team, sorted alphabetically by last name
        # Create a list of (last_name, full_name) tuples for proper sorting
        player_names = team_df['player_name'].unique()
        player_list = []
        for name in player_names:
            # Extract last name (assumed to be last word)
            parts = name.split()
            last_name = parts[-1] if parts else name
            player_list.append((last_name, name))
        
        # Sort by last name, then get player data
        player_list.sort(key=lambda x: x[0])
        
        players = []
        for _, full_name in player_list:
            player_data = self._calculate_player_stats(team_df, full_name, games_to_qualify, self.enhanced_data)
            players.append(player_data)
        
        return {
            "name": team_name,
            "players": players
        }
    
    def _calculate_player_stats(self, team_df, player_name: str, games_to_qualify_threshold: int, enhanced_data: Dict = None) -> Dict:
        """Calculate comprehensive player statistics."""
        player_df = team_df[team_df['player_name'] == player_name]
        
        if len(player_df) == 0:
            # Return empty stats for players with no data
            return self._empty_player_stats(player_name, games_to_qualify_threshold)
        
        # Calculate basic stats
        legs_played = len(player_df)
        games_played = self._estimate_games_played(player_df)
        games_remaining = max(0, games_to_qualify_threshold - games_played)
        eligibility = "QUALIFIED" if games_played >= games_to_qualify_threshold else "INELIGIBLE"
        
        # Calculate game-specific W/L records
        game_stats = self._calculate_game_specific_stats(player_df)
        
        # Calculate total wins/losses
        total_wins = sum([game_stats[game]['wins'] for game in game_stats])
        total_losses = sum([game_stats[game]['losses'] for game in game_stats])
        
        # Calculate win percentage
        total_games = total_wins + total_losses
        win_pct = f"{(total_wins / total_games * 100):.2f}%" if total_games > 0 else "0.00%"
        
        # Calculate QPs properly using CSV data for 501 and enhanced data for Cricket
        qps = self._calculate_total_qps(player_df, player_name, enhanced_data)
        qp_pct = f"{(qps / legs_played * 100):.2f}%" if legs_played > 0 else "0.00%"
        
        # Calculate rating
        if games_played > 0:
            rating = ((total_wins * 2) / games_played) + (qps / legs_played)
            rating = f"{rating:.4f}"
        else:
            rating = "0.0000"
        
        return {
            "name": player_name,  # Full name from data
            "legs": legs_played,
            "games": games_played,
            "qualify": games_remaining,
            "eligibility": eligibility,
            "s01_w": game_stats.get('501 SIDO', {}).get('wins', 0),
            "s01_l": game_stats.get('501 SIDO', {}).get('losses', 0),
            "sc_w": game_stats.get('Cricket', {}).get('wins', 0),
            "sc_l": game_stats.get('Cricket', {}).get('losses', 0),
            "d01_w": 0,  # Would need doubles data
            "d01_l": 0,  # Would need doubles data
            "dc_w": 0,   # Would need doubles data
            "dc_l": 0,   # Would need doubles data
            "total_w": total_wins,
            "total_l": total_losses,
            "win_pct": win_pct,
            "qps": qps,
            "qp_pct": qp_pct,
            "rating": rating
        }
    
    def _estimate_games_played(self, player_df):
        """Calculate actual games played by counting unique Set# combinations."""
        if len(player_df) == 0:
            return 0
        
        # Each unique combination of report_url + Set # represents one game
        if 'report_url' in player_df.columns and 'Set #' in player_df.columns:
            # Count unique games (Set numbers) across all matches
            games = player_df.groupby(['report_url', 'Set #']).ngroups
            return games
        else:
            # Fallback: estimate based on legs (best of 3, so ~2-3 legs per game)
            return max(1, len(player_df) // 3)
    
    def _calculate_game_specific_stats(self, player_df):
        """Calculate wins/losses by game type (counting games, not legs)."""
        stats = {}
        
        if 'report_url' not in player_df.columns or 'Set #' not in player_df.columns:
            # Fallback: count legs if we don't have Set # info
            for game_type in player_df['game_name'].unique():
                game_df = player_df[player_df['game_name'] == game_type]
                wins = len(game_df[game_df['win'] == 'W'])
                losses = len(game_df[game_df['win'] == 'L'])
                stats[game_type] = {'wins': wins, 'losses': losses}
            return stats
        
        # Proper calculation: determine who won each game (Set)
        for game_type in player_df['game_name'].unique():
            game_df = player_df[player_df['game_name'] == game_type]
            
            wins = 0
            losses = 0
            
            # Group by match and Set to determine game winners
            for (match_url, set_num), set_data in game_df.groupby(['report_url', 'Set #']):
                # Count legs won in this set
                legs_won = (set_data['win'] == 'W').sum()
                legs_lost = (set_data['win'] == 'L').sum()
                
                # Determine if player won this game (best of 3/5)
                if legs_won > legs_lost:
                    wins += 1
                elif legs_lost > legs_won:
                    losses += 1
                # If tied, it might be incomplete - count as neither for now
            
            stats[game_type] = {'wins': wins, 'losses': losses}
        
        return stats
    
    def _calculate_total_qps(self, player_df, player_name: str, enhanced_data: Dict = None) -> int:
        """Calculate total Quality Points from 501 (CSV) and Cricket (enhanced data)."""
        total_qps = 0
        
        # Calculate 501 QPs from CSV columns (Hi Turn and DO)
        total_qps += self._calculate_501_qps_from_csv(player_df)
        
        # Add Cricket QPs from enhanced data if available
        if enhanced_data:
            cricket_qps = self._get_cricket_qps_for_player(player_name, enhanced_data)
            total_qps += cricket_qps
        
        return total_qps
    
    def _calculate_501_qps_from_csv(self, player_df) -> int:
        """Calculate 501 QPs using Hi Turn and DO columns from CSV.
        
        QP Rules for 501:
        Turn Score QPs (Hi Turn):     Checkout QPs (DO):
        1: 95-115                     1: 61-84 out
        2: 116-131                    2: 85-106 out
        3: 132-147                    3: 107-128 out
        4: 148-163                    4: 129-150 out
        5: 164-180                    5: 151-170 out
        
        QPs are ADDITIVE - a leg can earn QPs from both columns!
        """
        total_qps = 0
        
        # Filter for 501 games only
        games_501 = player_df[player_df['game_name'] == '501 SIDO']
        
        for _, row in games_501.iterrows():
            leg_qps = 0
            
            # QPs from Hi Turn (high score in one turn)
            hi_turn = row.get('Hi Turn', 0)
            if pd.notna(hi_turn):
                try:
                    hi_turn = float(hi_turn)
                    if 164 <= hi_turn <= 180:
                        leg_qps += 5
                    elif 148 <= hi_turn <= 163:
                        leg_qps += 4
                    elif 132 <= hi_turn <= 147:
                        leg_qps += 3
                    elif 116 <= hi_turn <= 131:
                        leg_qps += 2
                    elif 95 <= hi_turn <= 115:
                        leg_qps += 1
                except (ValueError, TypeError):
                    pass
            
            # QPs from DO (checkout score)
            do_score = row.get('DO', 0)
            if pd.notna(do_score):
                try:
                    do_score = float(do_score)
                    if 151 <= do_score <= 170:
                        leg_qps += 5
                    elif 129 <= do_score <= 150:
                        leg_qps += 4
                    elif 107 <= do_score <= 128:
                        leg_qps += 3
                    elif 85 <= do_score <= 106:
                        leg_qps += 2
                    elif 61 <= do_score <= 84:
                        leg_qps += 1
                except (ValueError, TypeError):
                    pass
            
            total_qps += leg_qps
        
        return total_qps
    
    def _get_cricket_qps_for_player(self, player_name: str, enhanced_data: Dict) -> int:
        """Extract Cricket QPs for a player from enhanced data."""
        if not enhanced_data:
            return 0
        
        # Check if we have cricket QP data
        cricket_qp_data = enhanced_data.get('enhanced_statistics', {}).get('cricket_enhanced_qp', {})
        
        if player_name in cricket_qp_data:
            return cricket_qp_data[player_name].get('total_qp', 0)
        
        return 0
    
    def _empty_player_stats(self, player_name: str, games_to_qualify: int):
        """Return empty stats structure for players with no data."""
        return {
            "name": player_name,
            "legs": 0, "games": 0, "qualify": games_to_qualify, "eligibility": "INELIGIBLE",
            "s01_w": 0, "s01_l": 0, "sc_w": 0, "sc_l": 0,
            "d01_w": 0, "d01_l": 0, "dc_w": 0, "dc_l": 0,
            "total_w": 0, "total_l": 0, "win_pct": "0.00%",
            "qps": 0, "qp_pct": "0.00%", "rating": "0.0000"
        }
    
    def _create_team_section(self, team_data: Dict) -> List:
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
