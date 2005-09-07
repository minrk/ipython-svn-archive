<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: lists.mod.xsl,v 1.27 2004/12/05 09:29:15 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="variablelist/title|orderedlist/title|itemizedlist/title|simplelist/title">
		<xsl:param name="style" select="$latex.list.title.style"/>
		<xsl:text>
{</xsl:text>
		<xsl:value-of select="$style"/>
		<xsl:text>{</xsl:text>
		<xsl:apply-templates/>
		<xsl:text>}}
</xsl:text>
	</xsl:template><xsl:template match="listitem">
		<xsl:text>
%--- Item
</xsl:text>
		<xsl:text>\item </xsl:text>
		<xsl:apply-templates/>
		<xsl:text>
</xsl:text>
	</xsl:template><xsl:template match="itemizedlist">
		<xsl:apply-templates select="node()[not(self::listitem) and not(self::processing-instruction('db2latex-custom-list'))]"/>
		<xsl:call-template name="compactlist.pre"/>
		<xsl:text>
\begin{itemize}</xsl:text>
		<xsl:apply-templates select="processing-instruction('db2latex-custom-list')"/>
		<xsl:call-template name="compactlist.begin"/>
		<xsl:apply-templates select="listitem"/>
		<xsl:text>\end{itemize}
</xsl:text>
		<xsl:call-template name="compactlist.post"/>
	</xsl:template><xsl:template match="variablelist">
		<xsl:apply-templates select="node()[not(self::varlistentry) and not(self::processing-instruction('db2latex-custom-list'))]"/>
		<xsl:text>
\begin{description}
</xsl:text>
		<xsl:apply-templates select="processing-instruction('db2latex-custom-list')"/>
		<xsl:apply-templates select="varlistentry"/>
		<xsl:text>\end{description}
</xsl:text>
		<xsl:if test="$latex.use.noindent=1">
			<xsl:text>\noindent </xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="orderedlist">
		<xsl:variable name="numeration">
			<xsl:choose>
				<xsl:when test="@numeration">
					<xsl:value-of select="@numeration"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="arabic"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:apply-templates select="node()[not(self::listitem) and not(self::processing-instruction('db2latex-custom-list'))]"/>
		<xsl:call-template name="compactlist.pre"/>
		<xsl:text>
\begin{enumerate}</xsl:text>
		<xsl:apply-templates select="processing-instruction('db2latex-custom-list')"/>
		<xsl:if test="@numeration">
			<xsl:choose>
			<xsl:when test="@numeration='arabic'"> 	<xsl:text>[1]</xsl:text>
</xsl:when>
			<xsl:when test="@numeration='upperalpha'"><xsl:text>[A]</xsl:text>
</xsl:when>
			<xsl:when test="@numeration='loweralpha'"><xsl:text>[a]</xsl:text>
</xsl:when>
			<xsl:when test="@numeration='upperroman'"><xsl:text>[I]</xsl:text>
</xsl:when>
			<xsl:when test="@numeration='lowerroman'"><xsl:text>[i]</xsl:text>
</xsl:when>
			</xsl:choose>
		</xsl:if>
		<xsl:call-template name="compactlist.begin"/>
		<xsl:apply-templates select="listitem"/>
		<xsl:text>\end{enumerate}
</xsl:text>
		<xsl:call-template name="compactlist.post"/>
	</xsl:template><xsl:template match="varlistentry" name="varlistentry">
		<xsl:param name="next.is.list">
			<xsl:variable name="object" select="listitem/*[1]"/>
			<xsl:value-of select="count($object[self::itemizedlist or self::orderedlist or self::variablelist])"/>
		</xsl:param>
		<xsl:variable name="id">
			<xsl:call-template name="label.id"/>
		</xsl:variable>
		<xsl:text>% \null and \mbox are tricks to induce different typesetting decisions
</xsl:text>
		<xsl:text>\item[{</xsl:text>
		<xsl:for-each select="term">
			<xsl:apply-templates/>
			<xsl:if test="position()!=last()">
				<xsl:text>, </xsl:text>
			</xsl:if>
		</xsl:for-each>
		<xsl:choose>
			<xsl:when test="$next.is.list=1">
				<xsl:text>}]\mbox{}</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>}]\null{}</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:apply-templates select="listitem"/>
	</xsl:template><xsl:template match="varlistentry/term">
		<xsl:apply-templates/><xsl:text>, </xsl:text>
	</xsl:template><xsl:template match="varlistentry/listitem">
		<xsl:apply-templates/>
	</xsl:template><xsl:template name="generate.simplelist.tabular.string">
		<xsl:param name="cols" select="1"/>
		<xsl:param name="i" select="1"/>
		<xsl:choose>
			<xsl:when test="$i &gt; $cols"/>
			<xsl:otherwise>
			<xsl:text>l</xsl:text>
			<xsl:call-template name="generate.simplelist.tabular.string">
				<xsl:with-param name="i" select="$i+1"/>
				<xsl:with-param name="cols" select="$cols"/>
			</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="simplelist[@type='inline']" name="generate.simplelist.inline">
		<xsl:for-each select="member">
			<xsl:apply-templates/>
			<xsl:if test="position()!=last()">
				<xsl:text>, </xsl:text>
			</xsl:if>
		</xsl:for-each>
	</xsl:template><xsl:template match="simplelist[@type='horiz']" name="generate.simplelist.horiz">
		<xsl:param name="environment">
			<xsl:choose>
				<xsl:when test="$latex.use.ltxtable='1' or $latex.use.longtable='1'">
					<xsl:text>longtable</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>tabular</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:param name="cols">
			<xsl:choose>
			<xsl:when test="@columns">
				<xsl:value-of select="@columns"/>
			</xsl:when>
			<xsl:otherwise>1</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:text>
</xsl:text>
		<xsl:text>\begin{</xsl:text>
		<xsl:value-of select="$environment"/>
		<xsl:text>}{</xsl:text>
		<xsl:call-template name="generate.simplelist.tabular.string">
			<xsl:with-param name="cols" select="$cols"/>
		</xsl:call-template>
		<xsl:text>}
</xsl:text>
		<xsl:call-template name="simplelist.horiz">
			<xsl:with-param name="cols" select="$cols"/>
		</xsl:call-template>
		<xsl:text>
\end{</xsl:text>
		<xsl:value-of select="$environment"/>
		<xsl:text>}
</xsl:text>
	</xsl:template><xsl:template name="simplelist.horiz">
	<xsl:param name="cols">1</xsl:param>
	<xsl:param name="cell">1</xsl:param>
	<xsl:param name="members" select="./member"/>
	<xsl:if test="$cell &lt;= count($members)">
	    <xsl:text>
</xsl:text> 
	    <xsl:call-template name="simplelist.horiz.row">
		<xsl:with-param name="cols" select="$cols"/>
		<xsl:with-param name="cell" select="$cell"/>
		<xsl:with-param name="members" select="$members"/>
	    </xsl:call-template>
	    <xsl:text> \\</xsl:text> 
	    <xsl:call-template name="simplelist.horiz">
		<xsl:with-param name="cols" select="$cols"/>
		<xsl:with-param name="cell" select="$cell + $cols"/>
		<xsl:with-param name="members" select="$members"/>
	    </xsl:call-template>
	</xsl:if>
    </xsl:template><xsl:template name="simplelist.horiz.row">
	<xsl:param name="cols">1</xsl:param>
	<xsl:param name="cell">1</xsl:param>
	<xsl:param name="members" select="./member"/>
	<xsl:param name="curcol">1</xsl:param>
	<xsl:if test="$curcol &lt;= $cols">
	    <xsl:choose>
		<xsl:when test="$members[position()=$cell]">
		    <xsl:apply-templates select="$members[position()=$cell]"/>
		    <xsl:text> </xsl:text> 
		    <xsl:if test="$curcol &lt; $cols">
			<xsl:call-template name="generate.latex.cell.separator"/>
		    </xsl:if>
		</xsl:when>
	    </xsl:choose>
	    <xsl:call-template name="simplelist.horiz.row">
		<xsl:with-param name="cols" select="$cols"/>
		<xsl:with-param name="cell" select="$cell+1"/>
		<xsl:with-param name="members" select="$members"/>
		<xsl:with-param name="curcol" select="$curcol+1"/>
	    </xsl:call-template>
	</xsl:if>
    </xsl:template><xsl:template match="simplelist|simplelist[@type='vert']" name="generate.simplelist.vert">
		<xsl:param name="environment">
			<xsl:choose>
				<xsl:when test="$latex.use.ltxtable='1' or $latex.use.longtable='1'">
					<xsl:text>longtable</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>tabular</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:param name="cols">
			<xsl:choose>
			<xsl:when test="@columns">
				<xsl:value-of select="@columns"/>
			</xsl:when>
			<xsl:otherwise>1</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:text>
</xsl:text>
		<xsl:text>\begin{</xsl:text>
		<xsl:value-of select="$environment"/>
		<xsl:text>}{</xsl:text>
		<xsl:call-template name="generate.simplelist.tabular.string">
			<xsl:with-param name="cols" select="$cols"/>
		</xsl:call-template>
		<xsl:text>}
</xsl:text> 
		<xsl:call-template name="simplelist.vert">
			<xsl:with-param name="cols" select="$cols"/>
		</xsl:call-template>
		<xsl:text>
\end{</xsl:text>
		<xsl:value-of select="$environment"/>
		<xsl:text>}
</xsl:text>
	</xsl:template><xsl:template name="simplelist.vert">
	<xsl:param name="cols">1</xsl:param>
	<xsl:param name="cell">1</xsl:param>
	<xsl:param name="members" select="./member"/>
	<xsl:param name="rows" select="floor((count($members)+$cols - 1) div $cols)"/>
	<xsl:if test="$cell &lt;= $rows">
	    <xsl:text>
</xsl:text> 
	    <xsl:call-template name="simplelist.vert.row">
		<xsl:with-param name="cols" select="$cols"/>
		<xsl:with-param name="rows" select="$rows"/>
		<xsl:with-param name="cell" select="$cell"/>
		<xsl:with-param name="members" select="$members"/>
	    </xsl:call-template>
	    <xsl:text> \\</xsl:text> 
	    <xsl:call-template name="simplelist.vert">
		<xsl:with-param name="cols" select="$cols"/>
		<xsl:with-param name="cell" select="$cell+1"/>
		<xsl:with-param name="members" select="$members"/>
		<xsl:with-param name="rows" select="$rows"/>
	    </xsl:call-template>
	</xsl:if>
    </xsl:template><xsl:template name="simplelist.vert.row">
	<xsl:param name="cols">1</xsl:param>
	<xsl:param name="rows">1</xsl:param>
	<xsl:param name="cell">1</xsl:param>
	<xsl:param name="members" select="./member"/>
	<xsl:param name="curcol">1</xsl:param>
	<xsl:if test="$curcol &lt;= $cols">
	    <xsl:choose>
		<xsl:when test="$members[position()=$cell]">
		    <xsl:apply-templates select="$members[position()=$cell]"/>
		    <xsl:text> </xsl:text> 
		    <xsl:if test="$curcol &lt; $cols">
			<xsl:call-template name="generate.latex.cell.separator"/>
		    </xsl:if>
		</xsl:when>
		<xsl:otherwise>
		</xsl:otherwise>
	    </xsl:choose>
	    <xsl:call-template name="simplelist.vert.row">
		<xsl:with-param name="cols" select="$cols"/>
		<xsl:with-param name="rows" select="$rows"/>
		<xsl:with-param name="cell" select="$cell+$rows"/>
		<xsl:with-param name="members" select="$members"/>
		<xsl:with-param name="curcol" select="$curcol+1"/>
	    </xsl:call-template>
	</xsl:if>
    </xsl:template><xsl:template match="member">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="segmentedlist">
		<xsl:apply-templates select="title|titleabbrev"/>
		<xsl:apply-templates select="seglistitem"/>
	</xsl:template><xsl:template match="segmentedlist/title">
		<xsl:param name="style" select="$latex.list.title.style"/>
		<xsl:text>
{</xsl:text>
		<xsl:value-of select="$style"/>
		<xsl:text>{</xsl:text>
		<xsl:apply-templates/>
		<xsl:text>}}\\
</xsl:text>
	</xsl:template><xsl:template match="segtitle">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="seglistitem">
		<xsl:apply-templates/>
		<xsl:choose>
			<xsl:when test="position()=last()"><xsl:text>

</xsl:text></xsl:when>
			<xsl:otherwise><xsl:text> \\
</xsl:text></xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="seg">
		<xsl:variable name="segnum" select="position()"/>
		<xsl:variable name="seglist" select="ancestor::segmentedlist"/>
		<xsl:variable name="segtitles" select="$seglist/segtitle"/>

		<!--
		Note: segtitle is only going to be the right thing in a well formed
		SegmentedList.  If there are too many Segs or too few SegTitles,
		you'll get something odd...maybe an error
		-->

		<xsl:text> {</xsl:text>
		<xsl:value-of select="$latex.segtitle.style"/>
		<xsl:text>{</xsl:text>
		<xsl:apply-templates select="$segtitles[$segnum=position()]"/>
		<xsl:text>:}} </xsl:text>
		<xsl:apply-templates/>
	</xsl:template><xsl:template name="compactlist.pre">
		<xsl:if test="@spacing='compact'">
			<xsl:if test="$latex.use.parskip=1">
				<xsl:text>
\docbooktolatexnoparskip</xsl:text>
			</xsl:if>
		</xsl:if>
	</xsl:template><xsl:template name="compactlist.begin">
		<xsl:if test="@spacing='compact' and $latex.use.parskip!=1">
			<xsl:text>\setlength{\itemsep}{-0.25em}
</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template name="compactlist.post">
		<xsl:if test="@spacing='compact' and $latex.use.parskip=1">
			<xsl:text>\docbooktolatexrestoreparskip
</xsl:text>
		</xsl:if>
		<xsl:if test="$latex.use.noindent=1">
			<xsl:text>\noindent </xsl:text>
		</xsl:if>
	</xsl:template></xsl:stylesheet>
