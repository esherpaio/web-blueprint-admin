function postBillings(data, silent = false) {
    const url = `/api/v1/billings`;
    return callApi("POST", url, data, "application/json", silent);
}

function getBillingsId(billingId, silent = false) {
    const url = `/api/v1/billings/${billingId}`;
    return callApi("GET", url, null, null, silent);
}

function patchBillingsId(billingId, data, silent = false) {
    const url = `/api/v1/billings/${billingId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function postCarts(silent = false) {
    const url = `/api/v1/carts`;
    return callApi("POST", url, null, null, silent);
}

function getCarts(silent = false) {
    const url = `/api/v1/carts`;
    return callApi("GET", url, null, null, silent);
}

function getCartsId(cartId, silent = false) {
    const url = `/api/v1/carts/${cartId}`;
    return callApi("GET", url, null, null, silent);
}

function patchCartsId(cartId, data, silent = false) {
    const url = `/api/v1/carts/${cartId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteCartsId(cartId, silent = false) {
    const url = `/api/v1/carts/${cartId}`;
    return callApi("DELETE", url, null, null, silent);
}

function getCartsIdItems(cartId, silent = false) {
    const url = `/api/v1/carts/${cartId}/items`;
    return callApi("GET", url, null, null, silent);
}

function postCartsIdItems(cartId, data, silent = false) {
    const url = `/api/v1/carts/${cartId}/items`;
    return callApi("POST", url, data, "application/json", silent);
}

function patchCartsIdItemsId(cartId, cartItemId, data, silent = false) {
    const url = `/api/v1/carts/${cartId}/items/${cartItemId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteCartsIdItemsId(cartId, cartItemId, silent = false) {
    const url = `/api/v1/carts/${cartId}/items/${cartItemId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postCategories(data, silent = false) {
    const url = `/api/v1/categories`;
    return callApi("POST", url, data, "application/json", silent);
}

function patchCategoriesId(categoryId, data, silent = false) {
    const url = `/api/v1/categories/${categoryId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteCategoriesId(categoryId, silent = false) {
    const url = `/api/v1/categories/${categoryId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postCategoriesIdItems(categoryId, data, silent = false) {
    const url = `/api/v1/categories/${categoryId}/items`;
    return callApi("POST", url, data, "application/json", silent);
}

function patchCategoriesIdItemsId(categoryId, itemId, data, silent = false) {
    const url = `/api/v1/categories/${categoryId}/items/${itemId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteCategoriesIdItemsId(categoryId, itemId, silent = false) {
    const url = `/api/v1/categories/${categoryId}/items/${itemId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postCountries(data, silent = false) {
    const url = `/api/v1/countries`;
    return callApi("POST", url, data, "application/json", silent);
}

function getCountries(silent = false) {
    const url = `/api/v1/countries`;
    return callApi("GET", url, null, null, silent);
}

function getCountriesId(countryId, silent = false) {
    const url = `/api/v1/countries/${countryId}`;
    return callApi("GET", url, null, null, silent);
}

function patchCountriesId(countryId, data, silent = false) {
    const url = `/api/v1/countries/${countryId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteCountriesId(countryId, silent = false) {
    const url = `/api/v1/countries/${countryId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postCoupons(data, silent = false) {
    const url = `/api/v1/coupons`;
    return callApi("POST", url, data, "application/json", silent);
}

function deleteCouponsId(couponId, silent = false) {
    const url = `/api/v1/coupons/${couponId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postCurrencies(data, silent = false) {
    const url = `/api/v1/currencies`;
    return callApi("POST", url, data, "application/json", silent);
}

function getCurrencies(silent = false) {
    const url = `/api/v1/currencies`;
    return callApi("GET", url, null, null, silent);
}

function getCurrenciesId(currencyId, silent = false) {
    const url = `/api/v1/currencies/${currencyId}`;
    return callApi("GET", url, null, null, silent);
}

function deleteCurrenciesId(currencyId, silent = false) {
    const url = `/api/v1/currencies/${currencyId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postEmails(data, silent = false) {
    const url = `/api/v1/emails`;
    return callApi("POST", url, data, "application/json", silent);
}

function postLanguages(data, silent = false) {
    const url = `/api/v1/languages`;
    return callApi("POST", url, data, "application/json", silent);
}

function getLanguages(silent = false) {
    const url = `/api/v1/languages`;
    return callApi("GET", url, null, null, silent);
}

function getLanguagesId(languageId, silent = false) {
    const url = `/api/v1/languages/${languageId}`;
    return callApi("GET", url, null, null, silent);
}

function deleteLanguagesId(languageId, silent = false) {
    const url = `/api/v1/languages/${languageId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postOrders(data, silent = false) {
    const url = `/api/v1/orders`;
    return callApi("POST", url, data, "application/json", silent);
}

function patchOrdersId(orderId, data, silent = false) {
    const url = `/api/v1/orders/${orderId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteOrdersId(orderId, silent = false) {
    const url = `/api/v1/orders/${orderId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postOrdersIdPayments(orderId, data, silent = false) {
    const url = `/api/v1/orders/${orderId}/payments`;
    return callApi("POST", url, data, "application/json", silent);
}

function postOrdersIdRefunds(orderId, data, silent = false) {
    const url = `/api/v1/orders/${orderId}/refunds`;
    return callApi("POST", url, data, "application/json", silent);
}

function postProducts(data, silent = false) {
    const url = `/api/v1/products`;
    return callApi("POST", url, data, "application/json", silent);
}

function patchProductsId(productId, data, silent = false) {
    const url = `/api/v1/products/${productId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteProductsId(productId, silent = false) {
    const url = `/api/v1/products/${productId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postProductsIdLinks(productId, data, silent = false) {
    const url = `/api/v1/products/${productId}/links`;
    return callApi("POST", url, data, "application/json", silent);
}

function deleteProductsIdLinksId(productId, linkId, silent = false) {
    const url = `/api/v1/products/${productId}/links/${linkId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postProductsIdMedia(productId, data, silent = false) {
    const url = `/api/v1/products/${productId}/media`;
    return callApi("POST", url, data, false, silent);
}

function patchProductsIdMediaId(productId, mediaId, data, silent = false) {
    const url = `/api/v1/products/${productId}/media/${mediaId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteProductsIdMediaId(productId, mediaId, silent = false) {
    const url = `/api/v1/products/${productId}/media/${mediaId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postProductsIdOptions(productId, data, silent = false) {
    const url = `/api/v1/products/${productId}/options`;
    return callApi("POST", url, data, "application/json", silent);
}

function patchProductsIdOptionsId(productId, optionId, data, silent = false) {
    const url = `/api/v1/products/${productId}/options/${optionId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteProductsIdOptionsId(productId, optionId, silent = false) {
    const url = `/api/v1/products/${productId}/options/${optionId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postProductsIdSkus(productId, data, silent = false) {
    const url = `/api/v1/products/${productId}/skus`;
    return callApi("POST", url, data, "application/json", silent);
}

function postProductsIdValues(productId, data, silent = false) {
    const url = `/api/v1/products/${productId}/values`;
    return callApi("POST", url, data, "application/json", silent);
}

function patchProductsIdValuesId(productId, valueId, data, silent = false) {
    const url = `/api/v1/products/${productId}/values/${valueId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteProductsIdValuesId(productId, valueId, silent = false) {
    const url = `/api/v1/products/${productId}/values/${valueId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postRegions(data, silent = false) {
    const url = `/api/v1/regions`;
    return callApi("POST", url, data, "application/json", silent);
}

function getRegions(silent = false) {
    const url = `/api/v1/regions`;
    return callApi("GET", url, null, null, silent);
}

function getRegionsId(regionId, silent = false) {
    const url = `/api/v1/regions/${regionId}`;
    return callApi("GET", url, null, null, silent);
}

function deleteRegionsId(regionId, silent = false) {
    const url = `/api/v1/regions/${regionId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postSessions(data, silent = false) {
    const url = `/api/v1/sessions`;
    return callApi("POST", url, data, "application/json", silent);
}

function postSessionsGoogle(data, silent = false) {
    const url = `/api/v1/sessions/google`;
    return callApi("POST", url, data, "application/json", silent);
}

function deleteSessions(silent = false) {
    const url = `/api/v1/sessions`;
    return callApi("DELETE", url, null, "application/json", silent);
}

function getSettings(silent = false) {
    const url = `/api/v1/settings`;
    return callApi("GET", url, null, null, silent);
}

function patchSettings(data, silent = false) {
    const url = `/api/v1/settings`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function postOrdersIdShipments(orderId, data, silent = false) {
    const url = `/api/v1/orders/${orderId}/shipments`;
    return callApi("POST", url, data, "application/json", silent);
}

function postShipmentClasses(data, silent = false) {
    const url = `/api/v1/shipment-classes`;
    return callApi("POST", url, data, "application/json", silent);
}

function patchShipmentClassesId(shipmentClassId, data, silent = false) {
    const url = `/api/v1/shipment-classes/${shipmentClassId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteShipmentClassesId(shipmentClassId, silent = false) {
    const url = `/api/v1/shipment-classes/${shipmentClassId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postShipmentMethods(data, silent = false) {
    const url = `/api/v1/shipment-methods`;
    return callApi("POST", url, data, "application/json", silent);
}

function getShipmentMethods(data, silent = false) {
    const url = `/api/v1/shipment-methods`;
    return callApi("GET", url, data, null, silent);
}

function getShipmentMethodsId(shipmentMethodId, silent = false) {
    const url = `/api/v1/shipment-methods/${shipmentMethodId}`;
    return callApi("GET", url, null, null, silent);
}

function patchShipmentMethodsId(shipmentMethodId, data, silent = false) {
    const url = `/api/v1/shipment-methods/${shipmentMethodId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteShipmentMethodsId(shipmentMethodId, silent = false) {
    const url = `/api/v1/shipment-methods/${shipmentMethodId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postShipmentZones(data, silent = false) {
    const url = `/api/v1/shipment-zones`;
    return callApi("POST", url, data, "application/json", silent);
}

function patchShipmentZonesId(shipmentZoneId, data, silent = false) {
    const url = `/api/v1/shipment-zones/${shipmentZoneId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteShipmentZonesId(shipmentZoneId, silent = false) {
    const url = `/api/v1/shipment-zones/${shipmentZoneId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postShippings(data, silent = false) {
    const url = `/api/v1/shippings`;
    return callApi("POST", url, data, "application/json", silent);
}

function getShippingsId(shippingId, silent = false) {
    const url = `/api/v1/shippings/${shippingId}`;
    return callApi("GET", url, null, null, silent);
}

function patchShippingsId(shippingId, data, silent = false) {
    const url = `/api/v1/shippings/${shippingId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function postSkus(data, silent = false) {
    const url = `/api/v1/skus`;
    return callApi("POST", url, data, "application/json", silent);
}

function getSkus(data, silent = false) {
    const url = `/api/v1/skus`;
    return callApi("GET", url, data, null, silent);
}

function patchSkusId(skuId, data, silent = false) {
    const url = `/api/v1/skus/${skuId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function deleteSkusId(skuId, silent = false) {
    const url = `/api/v1/skus/${skuId}`;
    return callApi("DELETE", url, null, null, silent);
}

function postUsers(data, silent = false) {
    const url = `/api/v1/users`;
    return callApi("POST", url, data, "application/json", silent);
}

function getUsers(data, silent = false) {
    const url = `/api/v1/users`;
    return callApi("GET", url, data, null, silent);
}

function getUsersId(userId, silent = false) {
    const url = `/api/v1/users/${userId}`;
    return callApi("GET", url, null, null, silent);
}

function patchUsersId(userId, data, silent = false) {
    const url = `/api/v1/users/${userId}`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function postUsersIdActivation(userId, silent = false) {
    const url = `/api/v1/users/${userId}/activation`;
    return callApi("POST", url, {}, "application/json", silent);
}

function patchUsersIdActivation(userId, data, silent = false) {
    const url = `/api/v1/users/${userId}/activation`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function postUsersIdPassword(userId, silent = false) {
    const url = `/api/v1/users/${userId}/password`;
    return callApi("POST", url, {}, "application/json", silent);
}

function patchUsersIdPassword(userId, data, silent = false) {
    const url = `/api/v1/users/${userId}/password`;
    return callApi("PATCH", url, data, "application/json", silent);
}

function getVerifications(data, silent = false) {
    const url = `/api/v1/verifications`;
    return callApi("GET", url, data, null, silent);
}
