<!--############################################################################# 
|	$Id: foil.mod.xsl,v 1.1 2003/04/06 18:31:49 rcasellas Exp $
|- #############################################################################
|	$Author: rcasellas $
|														
|   PURPOSE:
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">


    <!--############################################################################# --><!-- DOCUMENTATION                                                                --><!--############################################################################# --><xsl:template match="foilgroup">
	<xsl:text>                                                                        

</xsl:text>
	<xsl:text>%---------------------------------------------------------------------- PART 
</xsl:text>
	<xsl:text>\part{</xsl:text><xsl:apply-templates select="title"/><xsl:text>            }
</xsl:text>
	<xsl:text>%---------------------------------------------------------------------- PART 
</xsl:text>
	<xsl:call-template name="label.id"/>
	<xsl:text>

</xsl:text>
	<xsl:apply-templates select="foil"/>
    </xsl:template><xsl:template match="foilgroup/title">
	<xsl:apply-templates/>
    </xsl:template><xsl:template match="foil">
	<xsl:text>
</xsl:text>
	<xsl:text>%---------------------------------------------------------------------- SLIDE 
</xsl:text>
	<xsl:text>\begin{slide}{</xsl:text>
	<xsl:apply-templates select="title"/>
	<xsl:text>}
</xsl:text>
	<xsl:call-template name="label.id"/>
	<xsl:text>
</xsl:text>
	<xsl:apply-templates select="*[not (self::title)]"/>
	<xsl:text>\end{slide}
</xsl:text>
    </xsl:template><xsl:template match="foil/title">
	<xsl:apply-templates/>
    </xsl:template></xsl:stylesheet>