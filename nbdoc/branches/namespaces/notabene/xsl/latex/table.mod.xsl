<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: table.mod.xsl,v 1.33 2004/12/05 09:55:00 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="table">
		<xsl:choose>
			<xsl:when test="caption">
				<xsl:message>Cannot cope with new-style tables lacking tgroup -- skipped.</xsl:message>
			</xsl:when>
			<xsl:when test="$latex.use.ltxtable='1'">
				<!--
				<xsl:message>No captions for ltxtable, yet.</xsl:message>
				-->
				<!--
				Can use captions with longtable, but this is handled by
				the thead and tfoot templates :-(
				-->
				<xsl:call-template name="content-templates"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:variable name="placement">
					<xsl:call-template name="generate.formal.title.placement">
						<xsl:with-param name="object" select="local-name(.)"/>
					</xsl:call-template>
				</xsl:variable>
				<xsl:variable name="position">
					<xsl:call-template name="generate.latex.float.position">
						<xsl:with-param name="default" select="'htb'"/>
					</xsl:call-template>
				</xsl:variable>
				<xsl:variable name="caption">
					<xsl:call-template name="generate.table.caption"/>
				</xsl:variable>
				<xsl:call-template name="map.begin">
					<xsl:with-param name="string" select="$position"/>
				</xsl:call-template>
				<xsl:if test="$placement='before' and $caption!=''">
					<xsl:text>\captionswapskip{}</xsl:text>
					<xsl:value-of select="$caption"/>
					<xsl:text>\captionswapskip{}</xsl:text>
				</xsl:if>
				<xsl:call-template name="content-templates"/>
				<xsl:if test="$placement!='before'"><xsl:value-of select="$caption"/></xsl:if>
				<xsl:call-template name="map.end">
					<xsl:with-param name="string" select="$position"/>
				</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template name="generate.table.caption.longtable">
		<xsl:for-each select="ancestor-or-self::table">
			<xsl:if test="not(./processing-instruction('db2latex-no-caption'))">
				<xsl:text>\caption{</xsl:text>
				<xsl:value-of select="$latex.table.caption.style"/>
				<xsl:text>{</xsl:text>
				<xsl:apply-templates select="title" mode="caption.mode"/>
				<xsl:text>}</xsl:text>
				<xsl:call-template name="label.id"/>
				<xsl:text>}\hypertarget{</xsl:text>
				<xsl:call-template name="generate.label.id"/>
				<xsl:text>}{}
</xsl:text>
			</xsl:if>
		</xsl:for-each>
	</xsl:template><xsl:template name="generate.table.caption">
		<xsl:for-each select="ancestor-or-self::table">
			<xsl:if test="not(./processing-instruction('db2latex-no-caption'))">
				<xsl:text>{</xsl:text>
				<xsl:value-of select="$latex.table.caption.style"/>
				<xsl:text>{\caption{</xsl:text>
				<xsl:apply-templates select="title" mode="caption.mode"/>
				<xsl:text>}</xsl:text>
				<xsl:call-template name="label.id"/>
				<xsl:text>}}
</xsl:text>
			</xsl:if>
		</xsl:for-each>
	</xsl:template><xsl:template match="informaltable">
		<xsl:call-template name="map.begin"/>
		<xsl:apply-templates/>
		<xsl:call-template name="map.end"/>
	</xsl:template><xsl:template name="table.format.tabularx">
		<xsl:param name="cols" select="1"/>
		<xsl:param name="i" select="1"/>
		<xsl:param name="colsep" select="1"/>
		<!-- sum of numeric portions in 1*-like colwidths -->
		<xsl:param name="starfactor" select="0"/>
		<xsl:choose>
			<!-- Out of the recursive iteration -->
			<xsl:when test="$i &gt; $cols"/>
			<!-- There are still columns to count -->
			<xsl:otherwise>
			<xsl:variable name="userwidth">
				<xsl:choose>
					<xsl:when test="./colspec[@colnum=$i]">
						<xsl:value-of select="./colspec[@colnum=$i]/@colwidth"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="./colspec[position()=$i]/@colwidth"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>
			<xsl:variable name="useralign">
				<xsl:choose>
					<xsl:when test="./colspec[@colnum=$i]/@align!=''">
						<xsl:value-of select="./colspec[@colnum=$i]/@align"/>
					</xsl:when>
					<xsl:when test="./colspec[position()=$i]/@align!=''">
						<xsl:value-of select="./colspec[position()=$i]/@align"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="./@align"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>
			<xsl:variable name="width">
				<xsl:variable name="cells" select="thead/row/entry[$i]|tbody/row/entry[$i]"/>
				<xsl:choose>
					<xsl:when test="string-length($userwidth)=0 and count($cells//itemizedlist|$cells//orderedlist|$cells//variablelist)&gt;0">
						<!-- In these specific circumstances, we MUST use a line-wrapped column
							 and yet the user hasn't specified one. -->
						<xsl:value-of select="'1*'"/>
					</xsl:when>
					<xsl:otherwise>
						<!-- In the general case, we just do what the user wants (may even
							 have no pre-specified width). -->
						<xsl:value-of select="$userwidth"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>
			<!-- Try to take heed of colspecs -->
			<xsl:choose>
				<xsl:when test="$width!=''">
					<xsl:text>&gt;{</xsl:text>
					<xsl:if test="contains($width,'*')">
						<!-- see tabularx documentation -->
						<xsl:text>\hsize=</xsl:text>
						<xsl:value-of select="substring-before($width,'*') * $starfactor"/>
						<xsl:text>\hsize</xsl:text>
					</xsl:if>
					<xsl:choose>
						<xsl:when test="$useralign='left'"><xsl:text>\RaggedRight</xsl:text></xsl:when>
						<xsl:when test="$useralign='right'"><xsl:text>\RaggedLeft</xsl:text></xsl:when>
						<xsl:when test="$useralign='center'"><xsl:text>\Centering</xsl:text></xsl:when>
						<xsl:when test="$useralign='char' and $latex.use.dcolumn='1'">
							<xsl:variable name="char" select="(./colspec[@colnum=$i]/@char|./colspec[position()=$i]/@char)[1]"/>
							<xsl:choose>
								<xsl:when test="$char=''"><xsl:text>d</xsl:text></xsl:when>
								<xsl:otherwise>D{<xsl:value-of select="$char"/>}{<xsl:value-of select="$char"/>}{-1}</xsl:otherwise>
							</xsl:choose>
						</xsl:when>
						<xsl:when test="$useralign!=''"><xsl:message>Table column '<xsl:value-of select="$useralign"/>' alignment is not supported.</xsl:message></xsl:when>
					</xsl:choose>
					<xsl:text>}</xsl:text>
					<xsl:choose>
						<xsl:when test="contains($width,'*')">
							<xsl:text>X</xsl:text>
						</xsl:when>
						<xsl:otherwise>
							<xsl:text>p{</xsl:text><xsl:value-of select="$width"/><xsl:text>}</xsl:text>
						</xsl:otherwise>
					</xsl:choose>
					<xsl:if test="$i&lt;$cols and $colsep='1'">
						<xsl:text>|</xsl:text>
					</xsl:if>
				</xsl:when>
				<xsl:otherwise>
					<xsl:choose>
						<xsl:when test="$useralign='left'"><xsl:text>l</xsl:text></xsl:when>
						<xsl:when test="$useralign='right'"><xsl:text>r</xsl:text></xsl:when>
						<xsl:when test="$useralign='center'"><xsl:text>c</xsl:text></xsl:when>
						<xsl:when test="$useralign='justify'"><xsl:text>X</xsl:text></xsl:when>
						<xsl:when test="$useralign='char' and $latex.use.dcolumn='1'">
							<xsl:variable name="char" select="(./colspec[@colnum=$i]/@char|./colspec[position()=$i]/@char)[1]"/>
							<xsl:choose>
								<xsl:when test="$char=''"><xsl:text>d</xsl:text></xsl:when>
								<xsl:otherwise>D{<xsl:value-of select="$char"/>}{<xsl:value-of select="$char"/>}{-1}</xsl:otherwise>
							</xsl:choose>
						</xsl:when>
						<xsl:otherwise>
							<xsl:text>c</xsl:text>
							<xsl:if test="$useralign!=''">
								<xsl:message>Table column '<xsl:value-of select="$useralign"/>' alignment is not supported.</xsl:message>
							</xsl:if>
						</xsl:otherwise>
					</xsl:choose>
					<xsl:if test="$i&lt;$cols and $colsep='1'">
						<xsl:text>|</xsl:text>
					</xsl:if>
				</xsl:otherwise>
			</xsl:choose>
			<!-- Recursive for next column -->
			<xsl:call-template name="table.format.tabularx">
				<xsl:with-param name="i" select="$i+1"/>
				<xsl:with-param name="cols" select="$cols"/>
				<xsl:with-param name="colsep" select="$colsep"/>
				<xsl:with-param name="starfactor" select="$starfactor"/>
			</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template name="table.format.tabular">
		<xsl:param name="cols" select="1"/>
		<xsl:param name="i" select="1"/>
		<xsl:param name="colsep" select="1"/>
		<xsl:choose>
			<!-- Out of the recursive iteration -->
			<xsl:when test="$i &gt; $cols"/>
			<!-- There are still columns to count -->
			<xsl:otherwise>
			<!-- Try to take heed of colspecs -->
			<xsl:variable name="width">
				<xsl:variable name="userwidth">
					<xsl:choose>
						<xsl:when test="./colspec[@colnum=$i]">
							<xsl:value-of select="./colspec[@colnum=$i]/@colwidth"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="./colspec[position()=$i]/@colwidth"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:variable name="cells" select="thead/row/entry[$i]|tbody/row/entry[$i]"/>
				<xsl:choose>
					<xsl:when test="string-length($userwidth)=0 and count($cells//itemizedlist|$cells//orderedlist|$cells//variablelist)&gt;0">
						<!-- In these specific circumstances, we MUST use a line-wrapped column
							 and yet the user hasn't specified one. -->
						<xsl:value-of select="concat(1 div $cols,'\linewidth')"/>
					</xsl:when>
					<xsl:otherwise>
						<!-- In the general case, we just do what the user wants (may even
							 have no pre-specified width). -->
						<xsl:value-of select="$userwidth"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>
			<xsl:variable name="useralign">
				<xsl:choose>
					<xsl:when test="./colspec[@colnum=$i]/@align!=''">
						<xsl:value-of select="./colspec[@colnum=$i]/@align"/>
					</xsl:when>
					<xsl:when test="./colspec[position()=$i]/@align!=''">
						<xsl:value-of select="./colspec[position()=$i]/@align"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="./@align"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>
			<xsl:choose>
				<xsl:when test="$width!='' and not(contains($width,'*'))">
					<xsl:choose>
						<xsl:when test="$useralign='left'"><xsl:text>&gt;{\RaggedRight}</xsl:text></xsl:when>
						<xsl:when test="$useralign='right'"><xsl:text>&gt;{\RaggedLeft}</xsl:text></xsl:when>
						<xsl:when test="$useralign='center'"><xsl:text>&gt;{\Centering}</xsl:text></xsl:when>
						<xsl:when test="$useralign='char'"><xsl:message>Table column 'char' alignment is not supported when width specified.</xsl:message></xsl:when>
						<xsl:when test="$useralign!=''"><xsl:message>Table column '<xsl:value-of select="$useralign"/>' alignment is not supported.</xsl:message></xsl:when>
					</xsl:choose>
					<xsl:text>p{</xsl:text><xsl:value-of select="$width"/><xsl:text>}</xsl:text>
					<xsl:if test="$i&lt;$cols and $colsep='1'">
						<xsl:text>|</xsl:text>
					</xsl:if>
				</xsl:when>
				<xsl:otherwise>
					<xsl:choose>
						<xsl:when test="$useralign='left'"><xsl:text>l</xsl:text></xsl:when>
						<xsl:when test="$useralign='right'"><xsl:text>r</xsl:text></xsl:when>
						<xsl:when test="$useralign='center'"><xsl:text>c</xsl:text></xsl:when>
						<xsl:when test="$useralign='justify'"><xsl:text>l</xsl:text></xsl:when>
						<xsl:when test="$useralign='char' and $latex.use.dcolumn='1'">
							<xsl:variable name="char" select="(./colspec[@colnum=$i]/@char|./colspec[position()=$i]/@char)[1]"/>
							<xsl:choose>
								<xsl:when test="$char=''"><xsl:text>d</xsl:text></xsl:when>
								<xsl:otherwise>D{<xsl:value-of select="$char"/>}{<xsl:value-of select="$char"/>}{-1}</xsl:otherwise>
							</xsl:choose>
						</xsl:when>
						<xsl:otherwise>
							<xsl:text>c</xsl:text>
							<xsl:if test="$useralign!=''">
								<xsl:message>Table column '<xsl:value-of select="$useralign"/>' alignment is not supported.</xsl:message>
							</xsl:if>
						</xsl:otherwise>
					</xsl:choose>
					<xsl:if test="$i&lt;$cols and $colsep='1'">
						<xsl:text>|</xsl:text>
					</xsl:if>
				</xsl:otherwise>
			</xsl:choose>
			<!-- Recursive for next column -->
			<xsl:call-template name="table.format.tabular">
				<xsl:with-param name="i" select="$i+1"/>
				<xsl:with-param name="cols" select="$cols"/>
				<xsl:with-param name="colsep" select="$colsep"/>
			</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!-- See tabularx documentation. --><!-- For example, if we have a 1* column and a 3* column, then the
	     the hsizes for each column are (1/(1+3)*2) and (3/(1+3)*2).
		 The ratio of these to the star values (star values being 1 and 3)
		 is 2/(1+3).
		 BUT it is now very complicated because it takes into account columns
		 where the user has not specified a width but LaTeX requires a
		 fixed-width column (i.e. specialcols may vary).
		 Relies on there being (a) colspecs for every column or (b) no
		 colspecs.
	 --><xsl:template name="generate.starfactor">
		<xsl:param name="i" select="1"/>
		<xsl:param name="cols" select="count(colspec)"/>
		<xsl:param name="sum" select="0"/>
		<xsl:param name="specialcols" select="count(colspec[contains(@colwidth,'*')])"/>
		<xsl:choose>
			<xsl:when test="$i&lt;=$cols and colspec[position()=$i and contains(@colwidth,'*')]">
				<!-- a * column -->
				<xsl:call-template name="generate.starfactor">
					<xsl:with-param name="i" select="$i+1"/>
					<xsl:with-param name="cols" select="$cols"/>
					<xsl:with-param name="sum" select="$sum+substring-before(colspec[$i]/@colwidth,'*')"/>
					<xsl:with-param name="specialcols" select="$specialcols"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="$i&lt;=$cols">
				<!-- not a * column, but we are going to pretend that it is -->
				<xsl:variable name="cells" select="thead/row/entry[$i]|tbody/row/entry[$i]"/>
				<xsl:variable name="problems" select="count($cells//itemizedlist|$cells//orderedlist|$cells//variablelist)"/>
				<xsl:choose>
					<xsl:when test="$problems &gt; 0">
						<xsl:call-template name="generate.starfactor">
							<xsl:with-param name="i" select="$i+1"/>
							<xsl:with-param name="cols" select="$cols"/>
							<xsl:with-param name="sum" select="$sum+1"/>
							<xsl:with-param name="specialcols" select="$specialcols+1"/>
						</xsl:call-template>
					</xsl:when>
					<xsl:otherwise>
						<xsl:call-template name="generate.starfactor">
							<xsl:with-param name="i" select="$i+1"/>
							<xsl:with-param name="cols" select="$cols"/>
							<xsl:with-param name="sum" select="$sum"/>
							<xsl:with-param name="specialcols" select="$specialcols"/>
						</xsl:call-template>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$specialcols div $sum"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="tgroup" name="tgroup">
		<xsl:param name="width">
			<xsl:for-each select="..">
				<xsl:call-template name="generate.latex.width"/>
			</xsl:for-each>
		</xsl:param>
		<xsl:variable name="colsep">
			<xsl:choose>
				<xsl:when test="@colsep!=''">
					<xsl:value-of select="number(@colsep)"/>
				</xsl:when>
				<xsl:when test="../@colsep!=''">
					<xsl:value-of select="number(../@colsep)"/>
				</xsl:when>
				<xsl:otherwise>1</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="frame">
			<xsl:choose>
				<xsl:when test="string-length(../@frame)&lt;1">all</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="../@frame"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="colspecs" select="./colspec"/>
		<xsl:variable name="usex">
			<xsl:choose>
				<xsl:when test="$latex.use.ltxtable='1'">
					<xsl:text>0</xsl:text>
				</xsl:when>
				<!-- if there are lists within cells, we need tabularx -->
				<xsl:when test="$latex.use.tabularx=1 and (descendant::itemizedlist|descendant::orderedlist|descendant::variablelist)">
					<xsl:text>1</xsl:text>
				</xsl:when>
				<!-- if there are instances of 1*-style colwidths, we need tabularx -->
				<xsl:when test="$latex.use.tabularx=1 and contains(colspec/@colwidth,'*')">
					<xsl:text>1</xsl:text>
				</xsl:when>
				<!-- if there are colspecs with 'justify' alignment and no explicit width, we need tabularx -->
				<xsl:when test="$latex.use.tabularx=1 and count(colspec[@align='justify'])&gt;0">
					<xsl:text>1</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>0</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="useminipage">
			<!-- Hack to get around LaTeX issue with tabular (not necessary with tabularx).
			This is NOT a good solution, and has problems of its own, but at least the footnotes
			do not actually disappear (which is what would otherwise happen). -->
			<xsl:if test="count(.//footnote)!=0">1</xsl:if>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="$usex='1'">
				<xsl:text>\begin{tabularx}</xsl:text>
			</xsl:when>
			<xsl:when test="$latex.use.ltxtable='1'">
				<xsl:if test="parent::informaltable">
					<xsl:text>\addtocounter{table}{-1}</xsl:text>
				</xsl:if>
				<xsl:text>\begin{longtable}</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:if test="$useminipage='1'"><xsl:text>\begin{minipage}{\linewidth}
</xsl:text></xsl:if>
				<xsl:text>\begin{tabular}</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:choose>
			<xsl:when test="$width!=''">
				<xsl:text>{</xsl:text>
				<xsl:value-of select="$width"/>
				<xsl:text>}</xsl:text>
			</xsl:when>
			<xsl:when test="$usex='1'">
				<xsl:text>{\linewidth}</xsl:text>
			</xsl:when>
			<!-- otherwise, do not emit any explicit size -->
		</xsl:choose>
		<xsl:text>[t]</xsl:text>
		<xsl:text>{</xsl:text>
		<xsl:if test="$frame='all' or $frame='sides'">
			<xsl:text>|</xsl:text>
		</xsl:if>
		<xsl:variable name="cols">
			<xsl:choose>
				<xsl:when test="@cols">
					<xsl:value-of select="@cols"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="count(tbody/row[1]/entry)"/>
					<xsl:message>Warning: table's tgroup lacks cols attribute. Assuming <xsl:value-of select="count(tbody/row[1]/entry)"/>.</xsl:message>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="$usex=1">
				<xsl:call-template name="table.format.tabularx">
					<xsl:with-param name="cols" select="$cols"/>
					<xsl:with-param name="colsep" select="$colsep"/>
					<xsl:with-param name="starfactor">
						<xsl:call-template name="generate.starfactor">
							<xsl:with-param name="cols" select="$cols"/>
						</xsl:call-template>
					</xsl:with-param>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="table.format.tabular">
					<xsl:with-param name="cols" select="$cols"/>
					<xsl:with-param name="colsep" select="$colsep"/>
				</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:if test="$frame='all' or $frame='sides'">
			<xsl:text>|</xsl:text>
		</xsl:if>
		<xsl:text>}
</xsl:text>
		<xsl:variable name="thead.frame">
			<xsl:choose>
				<xsl:when test="$frame!='sides' and $frame!='none' and $frame!='bottom'">
					<xsl:value-of select="1"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="0"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="tfoot.frame">
			<xsl:choose>
				<xsl:when test="$frame!='sides' and $frame!='none' and $frame!='top'">
					<xsl:value-of select="1"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="0"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<!-- APPLY TEMPLATES -->
		<xsl:choose>
			<xsl:when test="$latex.use.ltxtable='1' and parent::table">
				<!-- for tables only, not informaltables -->
				<xsl:variable name="placement">
					<xsl:call-template name="generate.formal.title.placement">
						<xsl:with-param name="object" select="'table'"/>
					</xsl:call-template>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="$placement='before'">
						<xsl:choose>
							<xsl:when test="thead">
								<xsl:apply-templates select="thead" mode="longtable.caption">
									<xsl:with-param name="frame" select="$thead.frame"/>
								</xsl:apply-templates>
								<xsl:apply-templates select="thead" mode="longtable.caption.continuation">
									<xsl:with-param name="frame" select="$thead.frame"/>
								</xsl:apply-templates>
							</xsl:when>
							<xsl:otherwise>
								<xsl:call-template name="thead.longtable.caption">
									<xsl:with-param name="frame" select="$thead.frame"/>
								</xsl:call-template>
								<xsl:call-template name="thead.longtable.caption.continuation">
									<xsl:with-param name="frame" select="$thead.frame"/>
								</xsl:call-template>
							</xsl:otherwise>
						</xsl:choose>
						<xsl:apply-templates select="tfoot">
							<xsl:with-param name="frame" select="$tfoot.frame"/>
						</xsl:apply-templates>
						<xsl:if test="$tfoot.frame=1 and not(tfoot)">
							<xsl:text>\hline 
</xsl:text>
						</xsl:if>
						<xsl:apply-templates select="tbody"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:if test="$thead.frame=1 and not(thead)">
							<xsl:text>\hline 
</xsl:text>
						</xsl:if>
						<xsl:apply-templates select="thead">
							<xsl:with-param name="frame" select="$thead.frame"/>
						</xsl:apply-templates>
						<xsl:choose>
							<xsl:when test="tfoot">
								<xsl:apply-templates select="tfoot" mode="longtable.caption.continued">
									<xsl:with-param name="frame" select="$tfoot.frame"/>
								</xsl:apply-templates>
								<xsl:apply-templates select="tfoot" mode="longtable.caption">
									<xsl:with-param name="frame" select="$tfoot.frame"/>
								</xsl:apply-templates>
							</xsl:when>
							<xsl:otherwise>
								<xsl:call-template name="tfoot.longtable.caption.continued">
									<xsl:with-param name="frame" select="$tfoot.frame"/>
								</xsl:call-template>
								<xsl:call-template name="tfoot.longtable.caption">
									<xsl:with-param name="frame" select="$tfoot.frame"/>
								</xsl:call-template>
							</xsl:otherwise>
						</xsl:choose>
						<xsl:apply-templates select="tbody"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:if test="$thead.frame=1 and not(thead)">
					<xsl:text>\hline 
</xsl:text>
				</xsl:if>
				<xsl:apply-templates select="thead">
					<xsl:with-param name="frame" select="$thead.frame"/>
				</xsl:apply-templates>
				<xsl:apply-templates select="tbody"/>
				<xsl:apply-templates select="tfoot">
					<xsl:with-param name="frame" select="$tfoot.frame"/>
				</xsl:apply-templates>
				<xsl:if test="$tfoot.frame=1 and not(tfoot)">
					<xsl:text>\hline 
</xsl:text>
				</xsl:if>
			</xsl:otherwise>
		</xsl:choose>
		<!--                 -->
		<xsl:choose>
			<xsl:when test="$usex=1">
				<xsl:text>\end{tabularx}
</xsl:text>
			</xsl:when>
			<xsl:when test="$latex.use.ltxtable='1'">
				<xsl:text>\end{longtable}
</xsl:text>
				<!-- catcode touchup ARGH -->
				<xsl:call-template name="generate.latex.cell.separator">
					<xsl:with-param name="which" select="'post'"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>\end{tabular}
</xsl:text>
				<xsl:if test="$useminipage='1'"><xsl:text>\end{minipage}
</xsl:text></xsl:if>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="colspec"/><xsl:template match="spanspec"/><xsl:template match="thead">
		<xsl:param name="frame" select="0"/>
		<xsl:if test="$frame=1">
			<xsl:text>\hline 
</xsl:text>
		</xsl:if>
		<xsl:apply-templates/>
		<xsl:if test="$latex.use.ltxtable='1'">
			<xsl:text> \endhead
</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="thead" mode="longtable.caption" name="thead.longtable.caption">
		<xsl:param name="frame" select="0"/>
		<xsl:call-template name="generate.table.caption.longtable"/>
		<xsl:text>\\
</xsl:text><!-- or should this be \tabularnewline? -->
		<xsl:if test="$frame=1">
			<xsl:text>\hline 
</xsl:text>
		</xsl:if>
		<xsl:apply-templates select="row"/>
		<xsl:text> \endfirsthead
</xsl:text>
	</xsl:template><xsl:template match="thead" mode="longtable.caption.continuation" name="thead.longtable.caption.continuation">
		<xsl:param name="frame" select="0"/>
		<xsl:text>\caption[]{</xsl:text>
		<xsl:value-of select="$latex.table.caption.style"/>
		<xsl:text>{</xsl:text>
		<xsl:call-template name="gentext.template">
			<xsl:with-param name="context" select="'table'"/>
			<xsl:with-param name="name" select="'thead.continuation'"/>
		</xsl:call-template>
		<xsl:text>}}\\
</xsl:text><!-- or should this be \tabularnewline? -->
		<xsl:if test="$frame=1">
			<xsl:text>\hline 
</xsl:text>
		</xsl:if>
		<xsl:apply-templates select="row"/>
		<xsl:text> \endhead
</xsl:text>
	</xsl:template><xsl:template match="tfoot">
		<xsl:param name="frame" select="0"/>
		<xsl:apply-templates/>
		<xsl:if test="$frame=1">
			<xsl:text>\hline 
</xsl:text>
		</xsl:if>
		<xsl:if test="$latex.use.ltxtable='1'">
			<xsl:text> \endfoot
</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="tfoot" mode="longtable.caption" name="tfoot.longtable.caption">
		<xsl:param name="frame" select="0"/>
		<xsl:apply-templates select="row"/>
		<xsl:if test="$frame=1">
			<xsl:text>\hline 
</xsl:text>
		</xsl:if>
		<xsl:call-template name="generate.table.caption.longtable"/>
		<xsl:text>\\
</xsl:text><!-- or should this be \tabularnewline? -->
		<xsl:text> \endlastfoot
</xsl:text>
	</xsl:template><xsl:template match="tfoot" mode="longtable.caption.continued" name="tfoot.longtable.caption.continued">
		<xsl:param name="frame" select="0"/>
		<xsl:apply-templates select="row"/>
		<xsl:if test="$frame=1">
			<xsl:text>\hline 
</xsl:text>
		</xsl:if>
		<xsl:text>\caption[]{</xsl:text>
		<xsl:value-of select="$latex.table.caption.style"/>
		<xsl:text>{</xsl:text>
		<xsl:call-template name="gentext.template">
			<xsl:with-param name="context" select="'table'"/>
			<xsl:with-param name="name" select="'tfoot.continued'"/>
		</xsl:call-template>
		<xsl:text>}}\\
</xsl:text><!-- or should this be \tabularnewline? -->
		<xsl:text> \endfoot
</xsl:text>
	</xsl:template><xsl:template match="thead/row/entry">
		<xsl:call-template name="latex.entry.prealign"/>
		<xsl:call-template name="latex.thead.row.entry"/>
		<xsl:call-template name="latex.entry.postalign"/>
		<xsl:if test="position()&lt;last()">
				<!-- note that position(), and last() are not good because they don't account for XML comments -->
			<xsl:call-template name="generate.latex.cell.separator">
				<xsl:with-param name="which" select="'pre'"/>
			</xsl:call-template>
		</xsl:if>
	</xsl:template><xsl:template match="tfoot/row/entry">
		<xsl:call-template name="latex.entry.prealign"/>
		<xsl:call-template name="latex.tfoot.row.entry"/>
		<xsl:call-template name="latex.entry.postalign"/>
		<xsl:if test="position()&lt;last()">
				<!-- note that position(), and last() are not good because they don't account for XML comments -->
			<xsl:call-template name="generate.latex.cell.separator">
				<xsl:with-param name="which" select="'pre'"/>
			</xsl:call-template>
		</xsl:if> 
	</xsl:template><xsl:template match="tbody">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="tbody/row">
		<xsl:apply-templates/>
		<xsl:text> \tabularnewline
</xsl:text>
		<xsl:call-template name="generate.table.row.separator"/>
	</xsl:template><xsl:template match="thead/row">
		<xsl:apply-templates/>
		<xsl:text> \tabularnewline
</xsl:text>
		<xsl:call-template name="generate.table.row.separator"/>
	</xsl:template><xsl:template match="tfoot/row">
		<xsl:call-template name="generate.table.row.separator"/>
		<xsl:apply-templates/>
		<xsl:text> \tabularnewline
</xsl:text>
	</xsl:template><!-- The rule below the last row in the table is controlled by the 
	Frame attribute of the enclosing Table or InformalTable and the RowSep 
	of the last row is ignored. If unspecified, this attribute is 
	inherited from enclosing elements, rowsep=1 by default. --><xsl:template name="generate.table.row.separator">
		<xsl:param name="rowsep">
			<xsl:choose>
				<xsl:when test="ancestor::tgroup/@rowsep!=''">
					<xsl:value-of select="number(ancestor::tgroup/@rowsep)"/>
				</xsl:when>
				<xsl:when test="ancestor::tgroup/../@rowsep!=''">
					<xsl:value-of select="number(ancestor::tgroup/../@rowsep)"/>
				</xsl:when>
				<xsl:otherwise>1</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:variable name="parent_position" select="count(../preceding-sibling::node())+1"/>
		<xsl:variable name="grandparent_children" select="count(../../child::node())"/>
		<xsl:if test="$rowsep=1 and (position() != last() or $parent_position &lt; $grandparent_children)">
		<xsl:call-template name="table.row.separator"/>
		</xsl:if>
	</xsl:template><xsl:template name="table.row.separator">
		<xsl:text> \hline 
</xsl:text>
	</xsl:template><xsl:template match="tbody/row/entry">
	<xsl:call-template name="latex.entry.prealign"/>
	<xsl:apply-templates/>
	<xsl:call-template name="latex.entry.postalign"/>
	<xsl:if test="position()&lt;last()">
		<xsl:call-template name="generate.latex.cell.separator">
			<xsl:with-param name="which" select="'pre'"/>
		</xsl:call-template>
	</xsl:if> 
    </xsl:template><xsl:template name="latex.entry.prealign">
	<xsl:variable name="span">
		<xsl:choose>
			<xsl:when test="@spanname!=''">
				<xsl:variable name="spanname" select="@spanname"/>
				<xsl:call-template name="calculate.colspan">
					<xsl:with-param name="namest" select="../../../spanspec[@spanname=$spanname]/@namest"/>
					<xsl:with-param name="nameend" select="../../../spanspec[@spanname=$spanname]/@nameend"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="@namest!=''">
				<xsl:call-template name="calculate.colspan"/>
			</xsl:when>
			<xsl:otherwise>-1</xsl:otherwise>
		</xsl:choose>
	</xsl:variable>
	<!-- Remember: if multicolumn is present, generate.latex.cell.separator post needs to occur within multicolumn -->
	<xsl:if test="$span &gt; 1">
		<xsl:text>\multicolumn{</xsl:text>
		<xsl:value-of select="$span"/>
		<xsl:text>}{|</xsl:text><!-- TODO take heed of @colsep on BOTH sides!! -->
		<xsl:choose>
			<xsl:when test="@align='left'"><xsl:text>l</xsl:text></xsl:when>
			<xsl:when test="@align='right'"><xsl:text>r</xsl:text></xsl:when>
			<xsl:when test="@align='center'"><xsl:text>c</xsl:text></xsl:when>
			<xsl:when test="@align='char'">c<xsl:message>Table _entry_ 'char' alignment is not supported.</xsl:message></xsl:when>
			<xsl:otherwise>c</xsl:otherwise>
		</xsl:choose>
	<!-- use this as a hook for some general warnings -->
		<xsl:text>|}</xsl:text>
	</xsl:if>
	<!-- this is used when the entry's align spec wants to override the column default -->
	<xsl:if test="$span &lt; 1">
		<xsl:choose>
			<xsl:when test="@align='left'"><xsl:text>\docbooktolatexalignll </xsl:text></xsl:when>
			<xsl:when test="@align='right'"><xsl:text>\docbooktolatexalignrl </xsl:text></xsl:when>
			<xsl:when test="@align='center'"><xsl:text>\docbooktolatexaligncl </xsl:text></xsl:when>
			<xsl:when test="@align='char'"><xsl:message>Table _entry_ char alignment is not supported.</xsl:message></xsl:when>
		</xsl:choose>
	</xsl:if>
	<xsl:text>{</xsl:text>
	<xsl:call-template name="generate.latex.cell.separator">
		<xsl:with-param name="which" select="'post'"/>
	</xsl:call-template>
	<xsl:if test="@rotate='1'">
		<xsl:text>\rotatebox{90}</xsl:text>
		<xsl:if test="@align!=''"><xsl:message>entry[@rotate='1' and @align!=''] probably doesn't work.</xsl:message></xsl:if>
	</xsl:if>
	<xsl:text>{</xsl:text>
	<!-- use this as a hook for some general warnings -->
	<xsl:if test="@morerows!=''"><xsl:message>The morerows attribute is not supported.</xsl:message></xsl:if>
	</xsl:template><xsl:template name="latex.entry.postalign">
	<xsl:text>}}</xsl:text>
	<!-- this is used when the entry's align spec wants to override the column default -->
	<xsl:if test="@namest='' and @spanspec=''"><!-- TODO improve -->
		<xsl:choose>
			<xsl:when test="@align='left'"><xsl:text>\docbooktolatexalignlr </xsl:text></xsl:when>
			<xsl:when test="@align='right'"><xsl:text>\docbooktolatexalignrr </xsl:text></xsl:when>
			<xsl:when test="@align='center'"><xsl:text>\docbooktolatexaligncr </xsl:text></xsl:when>
		</xsl:choose>
	</xsl:if>
	</xsl:template><xsl:template name="process.cell">
	<xsl:param name="cellgi">td</xsl:param>
	<xsl:variable name="empty.cell" select="count(node()) = 0"/>

	<xsl:element name="{$cellgi}">
	    <xsl:if test="@morerows">
		<xsl:attribute name="rowspan">
		    <xsl:value-of select="@morerows+1"/>
		</xsl:attribute>
	    </xsl:if>
	    <xsl:if test="@namest">
		<xsl:attribute name="colspan">
		    <xsl:call-template name="calculate.colspan"/>
		</xsl:attribute>
	    </xsl:if>
	    <xsl:if test="@align">
		<xsl:attribute name="align">
		    <xsl:value-of select="@align"/>
		</xsl:attribute>
	    </xsl:if>
	    <xsl:if test="@char">
		<xsl:attribute name="char">
		    <xsl:value-of select="@char"/>
		</xsl:attribute>
	    </xsl:if>
	    <xsl:if test="@charoff">
		<xsl:attribute name="charoff">
		    <xsl:value-of select="@charoff"/>
		</xsl:attribute>
	    </xsl:if>
	    <xsl:if test="@valign">
		<xsl:attribute name="valign">
		    <xsl:value-of select="@valign"/>
		</xsl:attribute>
	    </xsl:if>

	    <xsl:choose>
		<xsl:when test="$empty.cell">
		    <xsl:text>&#xA0;</xsl:text>
		</xsl:when>
		<xsl:otherwise>
		    <xsl:apply-templates/>
		</xsl:otherwise>
	    </xsl:choose>
	</xsl:element>
    </xsl:template><xsl:template name="generate.colgroup">
	<xsl:param name="cols" select="1"/>
	<xsl:param name="count" select="1"/>
	<xsl:choose>
	    <xsl:when test="$count&gt;$cols"/>
	    <xsl:otherwise>
		<xsl:call-template name="generate.col">
		    <xsl:with-param name="countcol" select="$count"/>
		</xsl:call-template>
		<xsl:call-template name="generate.colgroup">
		    <xsl:with-param name="cols" select="$cols"/>
		    <xsl:with-param name="count" select="$count+1"/>
		</xsl:call-template>
	    </xsl:otherwise>
	</xsl:choose>
    </xsl:template><xsl:template name="generate.col">
	<xsl:param name="countcol">1</xsl:param>
	<xsl:param name="colspecs" select="./colspec"/>
	<xsl:param name="count">1</xsl:param>
	<xsl:param name="colnum">1</xsl:param>

	<xsl:choose>
	    <xsl:when test="$count&gt;count($colspecs)">
		<col/>
	    </xsl:when>
	    <xsl:otherwise>
		<xsl:variable name="colspec" select="$colspecs[$count=position()]"/>
		<xsl:variable name="colspec.colnum">
		    <xsl:choose>
			<xsl:when test="$colspec/@colnum">
			    <xsl:value-of select="$colspec/@colnum"/>
			</xsl:when>
			<xsl:otherwise>
			    <xsl:value-of select="$colnum"/>
			</xsl:otherwise>
		    </xsl:choose>
		</xsl:variable>

		<xsl:choose>
		    <xsl:when test="$colspec.colnum=$countcol">
			<col>
			    <xsl:if test="$colspec/@align">
				<xsl:attribute name="align">
				    <xsl:value-of select="$colspec/@align"/>
				</xsl:attribute>
			    </xsl:if>
			    <xsl:if test="$colspec/@char">
				<xsl:attribute name="char">
				    <xsl:value-of select="$colspec/@char"/>
				</xsl:attribute>
			    </xsl:if>
			    <xsl:if test="$colspec/@charoff">
				<xsl:attribute name="charoff">
				    <xsl:value-of select="$colspec/@charoff"/>
				</xsl:attribute>
			    </xsl:if>
			</col>
		    </xsl:when>
		    <xsl:otherwise>
			<xsl:call-template name="generate.col">
			    <xsl:with-param name="countcol" select="$countcol"/>
			    <xsl:with-param name="colspecs" select="$colspecs"/>
			    <xsl:with-param name="count" select="$count+1"/>
			    <xsl:with-param name="colnum">
				<xsl:choose>
				    <xsl:when test="$colspec/@colnum">
					<xsl:value-of select="$colspec/@colnum + 1"/>
				    </xsl:when>
				    <xsl:otherwise>
					<xsl:value-of select="$colnum + 1"/>
				    </xsl:otherwise>
				</xsl:choose>
			    </xsl:with-param>
			</xsl:call-template>
		    </xsl:otherwise>
		</xsl:choose>
	    </xsl:otherwise>
	</xsl:choose>

    </xsl:template><xsl:template name="colspec.colnum">
	<!-- when this macro is called, the current context must be an entry -->
	<xsl:param name="colname"/>
	<!-- .. = row, ../.. = thead|tbody, ../../.. = tgroup -->
	<xsl:param name="colspecs" select="../../../../tgroup/colspec"/>
	<xsl:param name="count">1</xsl:param>
	<xsl:param name="colnum">1</xsl:param>
	<xsl:choose>
	    <xsl:when test="$count&gt;count($colspecs)"/>
	    <xsl:otherwise>
		<xsl:variable name="colspec" select="$colspecs[$count=position()]"/>
		<!--
		<xsl:value-of select="$count"/>:
		<xsl:value-of select="$colspec/@colname"/>=
		<xsl:value-of select="$colnum"/>
		-->
		<xsl:choose>
		    <xsl:when test="$colspec/@colname=$colname">
			<xsl:choose>
			    <xsl:when test="$colspec/@colnum">
				<xsl:value-of select="$colspec/@colnum"/>
			    </xsl:when>
			    <xsl:otherwise>
				<xsl:value-of select="$colnum"/>
			    </xsl:otherwise>
			</xsl:choose>
		    </xsl:when>
		    <xsl:otherwise>
			<xsl:call-template name="colspec.colnum">
			    <xsl:with-param name="colname" select="$colname"/>
			    <xsl:with-param name="colspecs" select="$colspecs"/>
			    <xsl:with-param name="count" select="$count+1"/>
			    <xsl:with-param name="colnum">
				<xsl:choose>
				    <xsl:when test="$colspec/@colnum">
					<xsl:value-of select="$colspec/@colnum + 1"/>
				    </xsl:when>
				    <xsl:otherwise>
					<xsl:value-of select="$colnum + 1"/>
				    </xsl:otherwise>
				</xsl:choose>
			    </xsl:with-param>
			</xsl:call-template>
		    </xsl:otherwise>
		</xsl:choose>
	    </xsl:otherwise>
	</xsl:choose>
    </xsl:template><xsl:template name="colspec.colwidth">
	<!-- when this macro is called, the current context must be an entry -->
	<xsl:param name="colname"/>
	<!-- .. = row, ../.. = thead|tbody, ../../.. = tgroup -->
	<xsl:param name="colspecs" select="../../../../tgroup/colspec"/>
	<xsl:param name="count">1</xsl:param>
	<xsl:choose>
	    <xsl:when test="$count&gt;count($colspecs)"/>
	    <xsl:otherwise>
		<xsl:variable name="colspec" select="$colspecs[$count=position()]"/>
		<xsl:choose>
		    <xsl:when test="$colspec/@colname=$colname">
			<xsl:value-of select="$colspec/@colwidth"/>
		    </xsl:when>
		    <xsl:otherwise>
			<xsl:call-template name="colspec.colwidth">
			    <xsl:with-param name="colname" select="$colname"/>
			    <xsl:with-param name="colspecs" select="$colspecs"/>
			    <xsl:with-param name="count" select="$count+1"/>
			</xsl:call-template>
		    </xsl:otherwise>
		</xsl:choose>
	    </xsl:otherwise>
	</xsl:choose>
    </xsl:template><xsl:template name="calculate.colspan">
	<xsl:param name="namest" select="@namest"/>
	<xsl:param name="nameend" select="@nameend"/>
	<xsl:variable name="scol">
	    <xsl:call-template name="colspec.colnum">
		<xsl:with-param name="colname" select="$namest"/>
	    </xsl:call-template>
	</xsl:variable>
	<xsl:variable name="ecol">
	    <xsl:call-template name="colspec.colnum">
		<xsl:with-param name="colname" select="$nameend"/>
	    </xsl:call-template>
	</xsl:variable>
	<xsl:value-of select="$ecol - $scol + 1"/>
    </xsl:template><!-- write docs:
		The pre/post mechanism is to deal with multicolumn, which
		needs to be the first command within a cell.
	--><xsl:template name="generate.latex.cell.separator">
		<xsl:param name="which"/>
		<xsl:choose>
			<xsl:when test="$which='pre'">
				<xsl:if test="$latex.entities='catcode'">
					<xsl:text> \catcode`\&amp;=4</xsl:text>
				</xsl:if>
				<xsl:text> &amp; </xsl:text>
			</xsl:when>
			<xsl:when test="$which='post'">
				<xsl:if test="$latex.entities='catcode'">
					<xsl:text>\catcode`\&amp;=\active </xsl:text>
				</xsl:if>
			</xsl:when>
			<xsl:otherwise>
				<xsl:choose>
					<xsl:when test="$latex.entities='catcode'">
						<xsl:text> \catcode`\&amp;=4 &amp;\catcode`\&amp;=\active </xsl:text>
					</xsl:when>
					<xsl:otherwise>
						<xsl:text> &amp; </xsl:text>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template></xsl:stylesheet>
