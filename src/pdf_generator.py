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
    
    def generate_report1(self, data: Dict[str, Any]) -> str:
        """
        Generate the first PDF report (League Statistics Report).
        
        Args:
            data: Processed data dictionary
            
        Returns:
            Path to the generated PDF file
        """
        report_config = self.config.get_pdf_config('report1')
        filename = f"league_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4 if report_config.get('page_size') == 'A4' else letter,
            topMargin=0.8*inch,
            bottomMargin=0.8*inch,
            leftMargin=0.8*inch,
            rightMargin=0.8*inch
        )
        
        # Build content
        content = []
        
        # Title
        title = report_config.get('title', 'League Statistics Report')
        content.append(Paragraph(title, self.styles['CustomTitle']))
        content.append(Spacer(1, 20))
        
        # Generation info
        gen_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        content.append(Paragraph(f"Generated: {gen_time}", self.styles['Normal']))
        content.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        content.append(Spacer(1, 20))
        
        # League Summary
        content.extend(self._create_league_summary(data))
        
        # Player Rankings
        content.extend(self._create_player_rankings(data))
        
        # Statistics Tables
        content.extend(self._create_statistics_tables(data))
        
        # Charts (if enabled)
        if report_config.get('include_charts', True):
            content.extend(self._create_charts(data))
        
        # Build PDF
        doc.build(content)
        
        self.logger.info(f"Generated report 1: {filepath}")
        return str(filepath)
    
    def generate_report2(self, data: Dict[str, Any]) -> str:
        """
        Generate the second PDF report (Player Performance Report).
        
        Args:
            data: Processed data dictionary
            
        Returns:
            Path to the generated PDF file
        """
        report_config = self.config.get_pdf_config('report2')
        filename = f"player_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4 if report_config.get('page_size') == 'A4' else letter,
            topMargin=0.8*inch,
            bottomMargin=0.8*inch,
            leftMargin=0.8*inch,
            rightMargin=0.8*inch
        )
        
        # Build content
        content = []
        
        # Title
        title = report_config.get('title', 'Player Performance Report')
        content.append(Paragraph(title, self.styles['CustomTitle']))
        content.append(Spacer(1, 20))
        
        # Generation info
        gen_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        content.append(Paragraph(f"Generated: {gen_time}", self.styles['Normal']))
        content.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        content.append(Spacer(1, 20))
        
        # Individual Player Performance
        content.extend(self._create_individual_performance(data))
        
        # Performance Trends
        content.extend(self._create_performance_trends(data))
        
        # Detailed Statistics
        content.extend(self._create_detailed_statistics(data))
        
        # Build PDF
        doc.build(content)
        
        self.logger.info(f"Generated report 2: {filepath}")
        return str(filepath)
    
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
    
    def _create_charts(self, data: Dict[str, Any]) -> List:
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
