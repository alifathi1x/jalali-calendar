/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SearchModel } from "@web/search/search_model";

import { EventBus, toRaw } from "@odoo/owl";
import { domainFromTree, treeFromDomain } from "@web/core/tree_editor/condition_tree";
import { _t } from "@web/core/l10n/translation";
import { useGetDomainTreeDescription } from "@web/core/domain_selector/utils";
import { makeContext } from "@web/core/context";
import { Domain } from "@web/core/domain";
import { evaluateExpr } from "@web/core/py_js/py";
import { sortBy, groupBy } from "@web/core/utils/arrays";
import { deepCopy } from "@web/core/utils/objects";

import {
      constructDateDomain,
      DEFAULT_INTERVAL,
      getComparisonOptions,
      getIntervalOptions,
      getPeriodOptions,
      rankInterval,
      yearSelected,
} from "./searchbar_utils";

const { DateTime } = luxon;
patch(SearchModel.prototype, {
      setup(services) {
            // services
            const { field: fieldService, name: nameService, orm, user, view } = services;
            this.orm = orm;
            this.fieldService = fieldService;
            this.userService = user;
            this.viewService = view;
    
            this.getDomainTreeDescription = useGetDomainTreeDescription(fieldService, nameService);
    
            // used to manage search items related to date/datetime fields
            this.referenceMoment = DateTime.local();
            this.comparisonOptions = getComparisonOptions();
            this.intervalOptions = getIntervalOptions();
            this.optionGenerators = getPeriodOptions(this.referenceMoment);
      },
      getFullComparison() {
            let searchItem = null;
            for (const queryElem of this.query.slice().reverse()) {
                const item = this.searchItems[queryElem.searchItemId];
                if (item.type === "comparison") {
                    searchItem = item;
                    break;
                } else if (item.type === "favorite" && item.comparison) {
                    searchItem = item;
                    break;
                }
            }
            if (!searchItem) {
                return null;
            } else if (searchItem.type === "favorite") {
                return searchItem.comparison;
            }
            const { dateFilterId, comparisonOptionId } = searchItem;
            const {
                fieldName,
                fieldType,
                description: dateFilterDescription,
            } = this.searchItems[dateFilterId];
            const selectedGeneratorIds = this._getSelectedGeneratorIds(dateFilterId);
            // compute range and range description
            const { domain: range, description: rangeDescription } = constructDateDomain(
                this.referenceMoment,
                fieldName,
                fieldType,
                selectedGeneratorIds
            );
            // compute comparisonRange and comparisonRange description
            const { domain: comparisonRange, description: comparisonRangeDescription } =
                constructDateDomain(
                    this.referenceMoment,
                    fieldName,
                    fieldType,
                    selectedGeneratorIds,
                    comparisonOptionId
                );
            return {
                comparisonId: comparisonOptionId,
                fieldName,
                fieldDescription: dateFilterDescription,
                range: range.toList(),
                rangeDescription,
                comparisonRange: comparisonRange.toList(),
                comparisonRangeDescription,
            };
      },
      _getDateFilterDomain(dateFilter, generatorIds, key = "domain") {
            const { fieldName, fieldType } = dateFilter;
            const dateFilterRange = constructDateDomain(
                this.referenceMoment,
                fieldName,
                fieldType,
                generatorIds
            );
            return dateFilterRange[key];
      },

  });